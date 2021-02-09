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

def unroute(rule, app):
    url_map = app.url_map
    rules = []
    for r in url_map.iter_rules():
        if r.rule == rule:
            rules.append(r)
            url_map._remap = True
    for r in rules:
        url_map._rules.remove(r)
    keys = []
    for k in url_map._rules_by_endpoint.keys():
        rule_list = url_map._rules_by_endpoint[k]
        for r in rules:
            if r in rule_list:
                rule_list.remove(r)
                keys.append(k)
    for k in keys:
        rule_list = url_map._rules_by_endpoint[k]
        if len(rule_list) == 0:
            del url_map._rules_by_endpoint[k]
    url_map.update()

