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

import requests

METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}

path_cache = {}

def get(path, cache=True):
    if not cache:
        return fetch(path)
    else:
        if not path in path_cache:
            path_cache[path] = fetch(path)
        return path_cache[path]

def fetch(path):
    url = METADATA_URL + path
    r = requests.get(url, headers=METADATA_HEADERS)
    return r.text

