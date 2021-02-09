# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import helpers.errors
import helpers.ldap
from helpers.ldap import RESULT_KEY_DN, RESULT_KEY_ATTRIBUTES
import helpers.ad
from helpers.dictionaries import CaseInsensitiveDict
import uuid
from ldap3.protocol.formatters import formatters
from ldap import SCOPE_SUBTREE, SCOPE_BASE, SCOPE_ONELEVEL
import ldap.modlist
import base64
from enum import Enum

def binding_args(connection):
    return {
            'url': connection['ldapUrl'],
            'userId': connection['credentials']['user'],
            'password': connection['credentials']['password']
        }

def externalize(o):
    d = o.get(RESULT_KEY_ATTRIBUTES, {})
    return {
        RESULT_KEY_DN: o.get(RESULT_KEY_DN, ''),
        RESULT_KEY_ATTRIBUTES: {
            k: helpers.ad.format_attribute(k, d[k]) for k in d.keys()
        }
    }

def validate_attributes(d, raise_exception=True):
    valid = {}
    notok = []
    for k in d.keys():
        v = helpers.ad.validate_attribute(k, d[k])
#        print('{}: ({}) {} -> ({}) {}'.format(k, type(d[k]), d[k], type(v), str(v)))
        if type(v) is bool:
            if v:
                v = d[k]
                if not isinstance(v, list):
                    v = [v]
                valid[k] = [str(s).encode('utf-8') for s in v]
            else:
                notok.append(k)
        else:
            if not isinstance(v, list):
                v = [v]
#            for x in v:
#                print('{}: {} ({})'.format(k, x, type(x)))
            valid[k] = [s if isinstance(s, bytes) else str(s).encode('utf-8') for s in v]
    if raise_exception and len(notok) > 0:
        raise helpers.errors.ValidationError(notok)
    return valid

SearchBehavior = Enum('SearchBehavior', 'EXPECT_ONE EXPECT_ZERO_OR_MORE')
NO_ATTRIBUTES = ['']

class EmptyResultsError(helpers.errors.Error):
    def __init__(self, message = 'zero results'):
        super(EmptyResultsError, self).__init__(message)

class ReloadAfterModError(EmptyResultsError):
    def __init__(self, message = 'failed to reload resource'):
        super(ReloadAfterModError, self).__init__(message)

class NonUniqueResultsError(helpers.errors.Error):
    def __init__(self, message = 'non-unique results'):
        super(NonUniqueResultsError, self).__init__(message)

def search(context, base, scope=None, filter=None, attributes=None, behavior=SearchBehavior.EXPECT_ZERO_OR_MORE, empty_results_error=EmptyResultsError, non_unique_results_error=NonUniqueResultsError):
    args = {'base': base}
    if not scope is None:
        args['scope'] = scope
    if not filter is None:
        args['filter'] = filter
    if not attributes is None:
        args['attributes'] = attributes
    entries = context.search(**args)
    if behavior == SearchBehavior.EXPECT_ONE:
        if len(entries) == 0 and empty_results_error:
            raise empty_results_error()
        elif len(entries) > 1 and non_unique_results_error:
            raise non_unique_results_error()
    return entries

def get(connection, base, scope=None, filter=None, attributes=None):
    with helpers.ldap.SaslBindingContext(**binding_args(connection)) as context:
        return [externalize(o) for o in search(context, base, scope, filter, attributes)]

def delete(connection, base, scope=None,  filter=None):
    with helpers.ldap.SaslBindingContext(**binding_args(connection)) as context:
        context.delete(search(context, base, scope, filter, NO_ATTRIBUTES, behavior=SearchBehavior.EXPECT_ONE)[0][RESULT_KEY_DN])

def new_object_dn(container, attributes):
    ci = CaseInsensitiveDict(attributes)
    object_classes = helpers.ad.format_attribute('objectClass', ci['objectClass'])
    if 'organizationalunit' in object_classes:
        attr = 'ou'
    else:
        attr = 'cn'
    if attr in ci:
        val = helpers.ad.format_attribute(attr, ci[attr])
    elif 'name' in ci:
        val = helpers.ad.format_attribute('name', ci['name'])
    else:
        raise helpers.errors.MissingAttributeError(attr)
    return '{}={},{}'.format(attr, val[0] if isinstance(val, list) else val, container[RESULT_KEY_DN])

def create(connection, base, data, scope=None, filter=None, attributes=None):
    with helpers.ldap.SaslBindingContext(**binding_args(connection)) as context:
        container = search(context, base, scope, filter, NO_ATTRIBUTES, behavior=SearchBehavior.EXPECT_ONE)[0]
        validated = validate_attributes(data)
        dn = new_object_dn(container, validated)
        context.add(dn, ldap.modlist.addModlist(validated))
        return externalize(search(context, dn, scope=SCOPE_BASE, attributes=attributes, behavior=SearchBehavior.EXPECT_ONE, empty_results_error=ReloadAfterModError)[0])

def update(connection, base, data, scope=None, filter=None, attributes=None, partial=True):
    with helpers.ldap.SaslBindingContext(**binding_args(connection)) as context:
        old = search(context, base, scope, filter, attributes=None, behavior=SearchBehavior.EXPECT_ONE)[0]
        old_dn = old[RESULT_KEY_DN]
        new_dn = old_dn
        old_attrs = old[RESULT_KEY_ATTRIBUTES]
        new_attrs = validate_attributes(data)
        old_attrs_ci = CaseInsensitiveDict(old_attrs)
        new_attrs_ci = CaseInsensitiveDict(new_attrs)
        if len(new_attrs) != len(new_attrs_ci):
            raise helpers.errors.BadRequestException('Case collision in attribute keys')
        rdn_attr_key = old_dn.split(',')[0].split('=')[0]
        # check for rename
        if rdn_attr_key in old_attrs_ci and rdn_attr_key in new_attrs_ci:
            old_rdn = helpers.ad.format_attribute(rdn_attr_key, old_attrs_ci[rdn_attr_key])
            new_rdn = helpers.ad.format_attribute(rdn_attr_key, new_attrs_ci[rdn_attr_key])
            if old_rdn != new_rdn:
                new_rdn_formatted = '{}={}'.format(rdn_attr_key, new_rdn)
                new_dn = ','.join([new_rdn_formatted if i == 0 else s for i, s in enumerate(old_dn.split(','))])
                del old_attrs_ci[rdn_attr_key]
                del new_attrs_ci[rdn_attr_key]
                #print(new_dn)
                context.rename(old_dn, new_rdn_formatted)
        # build mod list - only delete attributes if not partial (patch)
        modlist = []
        for k in list(new_attrs_ci) if partial else list(old_attrs_ci):
            if (not partial) and k in old_attrs_ci and k not in new_attrs_ci:
                # delete
                modlist.append((ldap.MOD_DELETE, k, None))
            elif k not in old_attrs_ci or old_attrs_ci[k] != new_attrs_ci[k]:
                # update / replace
                modlist.append((ldap.MOD_REPLACE, k, new_attrs_ci[k]))
        #print(modlist)
        if len(modlist) > 0:
            context.modify(new_dn, modlist)
        return externalize(search(context, new_dn, scope=SCOPE_BASE, attributes=attributes, behavior=SearchBehavior.EXPECT_ONE, empty_results_error=ReloadAfterModError)[0])

