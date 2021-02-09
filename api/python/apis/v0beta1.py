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

from flask import Blueprint, request, jsonify, abort
import data.connections
import data.ad
import urllib.parse
import helpers.errors
import helpers.ad
from helpers.ldap import RESULT_KEY_DN, RESULT_KEY_ATTRIBUTES
from ldap import SCOPE_BASE, SCOPE_SUBTREE, SCOPE_ONELEVEL
from ldap import NO_SUCH_OBJECT, INVALID_DN_SYNTAX, FILTER_ERROR, OBJECT_CLASS_VIOLATION, ALREADY_EXISTS, LDAPError

bp = Blueprint('v0beta1', __name__, url_prefix='/v0beta1')

MESSAGE_UNEXPECTED_RESULT_COUNT = 'operation expects singular result'

def mask_pwd(d):
    d.get('credentials', {})['password'] = '******'
    return d

def ldap_error(status_code, e):
    print(e)
    return error(status_code, e.args[0]['desc'])

def error(status_code, message):
    response = jsonify({
        'message': message
        })
    response.status_code = status_code
    return response

def empty(status_code):
    response = jsonify({})
    response.status_code = status_code
    return response

@bp.route('/connections', methods=['GET'])
def connections_get():
    return jsonify([mask_pwd(x) for x in data.connections.get_all()])

@bp.route('/connections', methods=['POST'])
def connections_post():
    try:
        return jsonify(mask_pwd(data.connections.create(request.json))), 201
    except helpers.errors.AlreadyExistsException as e:
        return error(400, e.message)

@bp.route('/connections/<string:connection>', methods=['GET'])
def connection_get(connection):
    try:
        return mask_pwd(data.connections.get(connection))
    except helpers.errors.NotFoundException as e:
        return error(404, e.message)

@bp.route('/connections/<string:connection>', methods=['DELETE'])
def connection_delete(connection):
    try:
        data.connections.delete(connection)
        return empty(204)
    except helpers.errors.NotFoundException as e:
        return error(404, e.message)

@bp.route('/connections/<string:connection>', methods=['PUT', 'PATCH'])
def connection_putpatch(connection):
    try:
        return mask_pwd(data.connections.update(connection, request.json, partial=True if request.method=='PATCH' else False))
    except helpers.errors.NotFoundException as e:
        return error(404, e.message)
    except helpers.errors.Error as e:
        return error(400, e.message)

def arg_scope(arg):
    if arg == 'base':
        return SCOPE_BASE
    elif arg == 'one':
        return SCOPE_ONELEVEL
    elif arg == 'sub':
        return SCOPE_SUBTREE
    else: # default to subtree
        return SCOPE_SUBTREE

def arg_attributes(arg):
    return arg.split(',') if arg else None

@bp.route('/connections/<string:connection>/ldap/<string:base>', methods=['GET'])
def get_entries(connection, base):
    try:
        args = {
                'connection': data.connections.get(connection),
                'base': base,
                'filter': request.args.get('filter'),
                'attributes': arg_attributes(request.args.get('attributes')),
                'scope': arg_scope(request.args.get('scope'))
            }
        return jsonify(data.ad.get(**args))
    except NO_SUCH_OBJECT as e:
        return ldap_error(404, e)
    except LDAPError as e:
        return ldap_error(400, e)

@bp.route('/connections/<string:connection>/ldap/<string:base>', methods=['DELETE'])
def delete_entries(connection, base):
    try:
        args = {
                'connection': data.connections.get(connection),
                'base': base,
                'filter': request.args.get('filter'),
                'scope': arg_scope(request.args.get('scope'))
            }
        data.ad.delete(**args)
        return empty(200)
    except data.ad.EmptyResultsError as e:
        return error(404, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except data.ad.NonUniqueResultsError as e:
        return error(400, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except helpers.errors.Error as e:
        return error(400, e.message)
    except NO_SUCH_OBJECT as e:
        return ldap_error(404, e)
    except LDAPError as e:
        return ldap_error(400, e)

def deserialize(d):
    de = {}
    for k in d.keys():
        try:
            de[k] = helpers.json.deserialize_attribute(k, d[k])
        except Exception as e:
            raise ValueError('failed to deserialize attribute "{}". {}'.format(k, str(e)))
    return de

def validate_attributes(d):
    if not type(d) is dict:
        raise ValueError('dictionary expected')
    keys = list(d.keys())
    if not RESULT_KEY_ATTRIBUTES in keys:
        raise ValueError('key expected: %s' % RESULT_KEY_ATTRIBUTES)
    if len(keys) > 1:
        keys.remove(RESULT_KEY_ATTRIBUTES)
        raise ValueError('unexpected key(s): {}'.format(', '.join(keys)))
    return deserialize(d[RESULT_KEY_ATTRIBUTES])

@bp.route('/connections/<string:connection>/ldap/<string:base>', methods=['POST'])
def create_entry(connection, base):
    try:
        args = {
            'connection': data.connections.get(connection),
            'base': base,
            'filter': request.args.get('filter'),
            'scope': arg_scope(request.args.get('scope')),
            'data': validate_attributes(request.json),
            'attributes': arg_attributes(request.args.get('attributes'))
        }
        return jsonify([data.ad.create(**args)])
    except ValueError as e:
        return error(400, str(e))
    except data.ad.EmptyResultsError as e:
        return error(404, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except data.ad.NonUniqueResultsError as e:
        return error(400, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except helpers.errors.Error as e:
        return error(400, e.message)
    except LDAPError as e:
        return ldap_error(400, e)

@bp.route('/connections/<string:connection>/ldap/<string:base>', methods=['PUT', 'PATCH'])
def update_entry(connection, base):
    try:
        args = {
            'connection': data.connections.get(connection),
            'base': base,
            'filter': request.args.get('filter'),
            'scope': arg_scope(request.args.get('scope')),
            'data': validate_attributes(request.json),
            'attributes': arg_attributes(request.args.get('attributes')),
            'partial': True if request.method == 'PATCH' else False
        }
        return jsonify([data.ad.update(**args)])
    except ValueError as e:
        return error(400, str(e))
    except data.ad.EmptyResultsError as e:
        return error(404, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except data.ad.NonUniqueResultsError as e:
        return error(400, MESSAGE_UNEXPECTED_RESULT_COUNT)
    except helpers.errors.Error as e:
        return error(400, e.message)
    except LDAPError as e:
        return ldap_error(400, e)

