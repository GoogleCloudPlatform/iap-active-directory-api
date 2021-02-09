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

from flask.json import JSONEncoder
from datetime import datetime, timedelta, timezone
import base64
from  helpers.ad import attribute_type, custom_tuples, format_attribute_accountExpires, validate_attribute_unicodePwd
from ldap3.protocol.formatters.standard import find_attribute_helpers
from ldap3.protocol.formatters import formatters, validators

def deserialize_timestamp(v):
    # return naive datetime adjusted to utc
    return datetime.fromisoformat(v).astimezone(tz=timezone.utc).replace(tzinfo=None)

def deserialize_timedelta(v):
    return int(-10000000 * float(v))

def deserialize_binary(v):
    return base64.b64decode(v)

ATTRS_SHORT_CIRCUIT = [x.lower() for x in ['unicodePwd', 'userPassword']]

def deserialize_attribute(k, v):
    attr_type = attribute_type(k)
    attribute_helpers = find_attribute_helpers(attr_type, k, custom_tuples)
    formatter = formatters.format_unicode if not attribute_helpers[0] else attribute_helpers[0]
    validator = None if not attribute_helpers[1] else attribute_helpers[1]
    if not validator:
        if attr_type and attr_type.single_value:
            validator = validators.validate_generic_single_value
        else:
            validator = validators.always_valid
    # short-circuit deserialization for some known string attributes
    if k.lower() in ATTRS_SHORT_CIRCUIT:
        return v
    elif formatter is formatters.format_ad_timestamp:
        if validator is validators.validate_zero_and_minus_one_and_positive_int:
            return v # don't deserialize as timestamp b/c pwdLastSet should be literal 0 or -1, only system can set timestamp value
        else:
            return deserialize_timestamp(v) if not isinstance(v, list) else [deserialize_timestamp(i) for i in v]
    elif formatter is formatters.format_time:
        return deserialize_timestamp(v) if not isinstance(v, list) else [deserialize_timestamp(i) for i in v]
    elif formatter is formatters.format_ad_timedelta:
        return deserialize_timedelta(v) if not isinstance(v, list) else [deserialize_timedelta(i) for i in v]
    elif formatter is formatters.format_binary:
        return deserialize_binary(v) if not isinstance(v, list) else [deserialize_binary(i) for i in v]
    elif formatter is format_attribute_accountExpires:
        try:
            return deserialize_timestamp(v) if not isinstance(v, list) else [deserialize_timestamp(i) for i in v]
        except:
            return v # can be literal "never" so allow through if doesn't parse
    else:
        return v

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return obj.days * 86400 + obj.seconds + obj.microseconds / 1000000.0
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        else:
            return JSONEncoder.default(self, obj)

