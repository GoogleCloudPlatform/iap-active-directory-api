#!/usr/bin/env python

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

from google.oauth2 import id_token
import google.auth.transport.requests
import requests
import sys
import urllib
from urllib.parse import urlparse

host = urlparse(sys.argv[1]).netloc.split(':')[0]

response = requests.get("https://%s/" % ( host, ), allow_redirects = False)
query = urllib.parse.urlparse(response.headers["location"]).query
client_id = urllib.parse.parse_qs(query)["client_id"][0]

request = google.auth.transport.requests.Request()
open_id_connect_token = id_token.fetch_id_token(request, client_id)

print(open_id_connect_token)

