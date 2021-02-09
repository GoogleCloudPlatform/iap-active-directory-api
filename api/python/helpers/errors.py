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

class Error(Exception):
    def __init__(self, message):
        self.message = message 

class AlreadyExistsException(Error):

    def __init__(self, message = 'Resource already exists'):
        super(AlreadyExistsException, self).__init__(message)

class NotFoundException(Error):

    def __init__(self, message = 'Resource not found'):
        super(NotFoundException, self).__init__(message)

class BadRequestException(Error):

    def __init__(self, message = 'Bad request'):
        super(BadRequestException, self).__init__(message)

class ClientError(Error):
    def __init__(self, message):
        super(ClientError, self).__init__(message)

class NotFoundError(ClientError):
    def __init__(self):
        super(NotFoundError, self).__init__('resource not found')

class ValidationError(ClientError):
    def __init__(self, attrs):
        super(ValidationError, self).__init__('attribute validation failed: %s' % ( ', '.join(attrs) ))
        self.attrs = attrs

class MissingAttributeError(ClientError):
    def __init__(self, attr):
        super(MissingAttributeError, self).__init__('missing attribute(s): %s' % ( attr if not isinstance(attr, list) else ', '.join(attr) ))
        self.attrs = attr

def format_unicode_utf_16_le(v):
    return str(v, 'utf-16-le', errors='strict')

