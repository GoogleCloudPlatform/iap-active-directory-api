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

import os
import helpers.kms
import helpers.env
import helpers.metadata
import helpers.errors
from google.cloud import datastore

ds = datastore.Client()

def get_kms_tuple():
    return (
            helpers.env.get("KMS_PROJECT", helpers.metadata.get("project/project-id")),
            helpers.env.get("KMS_LOCATION"),
            helpers.env.get("KMS_KEYRING"),
            helpers.env.get("KMS_KEY")
            )

def encrypt(s):
    return helpers.kms.encrypt_symmetric(*get_kms_tuple(), s)

def decrypt(s):
    return helpers.kms.decrypt_symmetric(*get_kms_tuple(), s)

_kind = 'active-directory-user-management-api:connection'

def internalize(o, partial=False):
    d = {}
    missing = []
    if 'name' in o:
        d['name'] = o['name']
    else:
        missing.append('name')
    if 'ldapUrl' in o:
        d['ldap-url'] = o['ldapUrl']
    else:
        missing.append('ldapUrl')
    creds = o.get('credentials', {})
    if 'user' in creds:
        d['bind-user'] = creds['user']
    else:
        missing.append('credentials.user')
    if 'password' in creds:
        d['bind-password'] = encrypt(creds['password'])
    else:
        missing.append('credentials.password')
    if len(missing) > 0 and not partial:
        raise helpers.errors.MissingAttributeError(missing)
    else:
        return d

def externalize(o):
    return {
        'name': o['name'],
        'ldapUrl': o['ldap-url'],
        'credentials': {
            'user': o['bind-user'],
            'password': decrypt(o['bind-password'])
        }}

def get_all():
    q = ds.query(kind=_kind)
    return [externalize(x) for x in list(q.fetch())]

def get(name):
    q = ds.query(kind=_kind)
    q.add_filter('name', '=', name)
    l = list(q.fetch(limit=1))
    if len(l) < 1:
        raise helpers.errors.NotFoundException('Resource not found: {}'.format(name))
    else:
        return externalize(l[0])

def delete(name):
    with ds.transaction() as t:
        q = ds.query(kind=_kind)
        q.add_filter('name', '=', name)
        l = list(q.fetch(limit=1))
        if len(l) < 1:
            raise helpers.errors.NotFoundException('Resource not found: {}'.format(name))
        else:
            entity = l[0]
            t.delete(entity.key)

def create(data):
    with ds.transaction() as t:
        q = ds.query(kind=_kind)
        q.add_filter('name', '=', data['name'])
        l = list(q.fetch(limit=1))
        if len(l) > 0:
            raise helpers.errors.AlreadyExistsException('Resource already exists: {}'.format(data['name']))
        else:
            entity = datastore.Entity(ds.key(_kind))
            entity.update(internalize(data))
            t.put(entity)
            return externalize(entity)

def update(name, data, partial=False):
    if name != data.get('name', name):
        raise helpers.errors.BadRequestException('Resource name mismatch: {}'.format(data['name']))
    with ds.transaction() as t:
        q = ds.query(kind=_kind)
        q.add_filter('name', '=', name)
        l = list(q.fetch(limit=1))
        if len(l) < 1:
            raise helpers.errors.NotFoundException('Resource not found: {}'.format(name))
        else:
            entity = l[0]
            entity.update(internalize(data, partial=partial))
            t.put(entity)
            return externalize(entity)

