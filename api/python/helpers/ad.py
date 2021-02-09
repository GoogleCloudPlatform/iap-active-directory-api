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

from ldap3.protocol.schemas.ad2012R2 import ad_2012_r2_schema, ad_2012_r2_dsa_info
from ldap3.protocol.rfc4512 import SchemaInfo, DsaInfo
from ldap3.protocol.formatters.standard import standard_formatter, format_attribute_values, find_attribute_validator, find_attribute_helpers, validate_generic_single_value
from ldap3.protocol.formatters import standard, formatters, validators
from ldap3 import SEQUENCE_TYPES, STRING_TYPES
from ldap3.utils.conv import to_unicode
from datetime import datetime, timezone

schema = SchemaInfo.from_json(ad_2012_r2_schema)
info = DsaInfo.from_json(ad_2012_r2_dsa_info, schema)

def validate_attribute_unicodePwd(v):
    if isinstance(v, SEQUENCE_TYPES):
        v = v[0]
    if isinstance(v, str):
        if not (v.startswith('"') and v.endswith('"')):
            v = '"{}"'.format(v)
        return v.encode('utf-16-le')
    else:
        return False

MAX_DT_AD_BSTR = b'9223372036854775807'
MAX_DT_PY = datetime.max.replace(tzinfo=timezone.utc)
MAX_DT_PY_STR = 'never'

def validate_time_tenths(v):
    if isinstance(v, list):
        return [validate_time_tenths(x) for x in v]
    elif isinstance(v, datetime):
        if v.tzname():
            v = v.astimezone(tz=timezone.utc).replace(tzinfo=None)
        return '{}.0Z'.format(validators.validate_time(v)[0:-1])
    else:
        return validators.validate_time(v)

def format_attribute_accountExpires(v):
    # delegate to default formatter
    v = format_attribute('accountExpires', v, False)
    if isinstance(v, datetime) and v == MAX_DT_PY:
        return MAX_DT_PY_STR
    return v

def validate_attribute_accountExpires(v):
#    print(v)
#    print(type(v))
    changed = False
    if isinstance(v, datetime) and v == MAX_DT_PY:
        changed = True
        v = MAX_DT_AD_BSTR
    elif isinstance(v, str) and v.lower() == MAX_DT_PY_STR:
        changed = True
        v = MAX_DT_AD_BSTR
    # delegate to standard validator
    validated = validate_attribute('accountExpires', v, False) 
    # we replaced the value so if it validates and unless standard validator replaces it, return our value instead of True 
#    print(v)
#    print(validated)
    return v if changed and isinstance(validated, bool) and validated else validated

custom_formatter = {
    '1.2.840.113556.1.4.618': formatters.format_unicode,            # override binary with string for wellKnownObjects
    '1.2.840.113556.1.4.1359': formatters.format_unicode,           # override binary with string for otherWellKnownObjects
    '1.2.840.113556.1.4.159': format_attribute_accountExpires       # account for literal "never" and difference between AD and python max dates
    }

custom_validator = {
    '1.2.840.113556.1.4.90': validate_attribute_unicodePwd,         # unicodePwd requires special formatting/encoding
    '1.2.840.113556.1.4.159': validate_attribute_accountExpires,    # account for literal "never" and difference between AD and python max dates
    '1.3.6.1.4.1.1466.115.121.1.24': validate_time_tenths,          # reformat with .0 to match AD format
    '1.3.6.1.4.1.1466.115.121.1.53': validate_time_tenths,          # reformat with .0 to match AD format
    '2.16.840.1.113719.1.1.5.1.19': validate_time_tenths,           # reformat with .0 to match AD format
    }

def attribute_type(k):
    return schema.attribute_types.get(k, None)

custom_tuples = { # build dictionary of custom formatter and validator tuples filling in missing values from defaults
    k: (
        custom_formatter.get(k, standard.find_attribute_helpers(attribute_type(k), k, None)[0]),
        custom_validator.get(k, standard.find_attribute_helpers(attribute_type(k), k, None)[1])
    )
    for k in list(custom_formatter.keys()) + list(custom_validator.keys())
}

def attribute_formatter(oid):
    return standard_formatter.get(oid, (None, None))[0]

def attribute_validator(oid):
    return standard_formatter.get(oid, (None, None))[1]

def format_attribute(k, v, customize=True):
    return format_attribute_values(schema, k, v, custom_formatter if customize else None)

def validate_attribute(k, v, customize=True):
    f = find_attribute_validator(schema, k, custom_validator if customize else None)
#    print('{} ({}): {} ({}) -> {} ({})'.format(k, f, v, type(v), f(v), type(f(v))))
    return f(v)

