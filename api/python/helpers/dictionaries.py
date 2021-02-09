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

from collections import Mapping
from itertools import chain

class MutatedDict(dict):

    @classmethod
    def fromkeys(cls, keys, v=None):
        return cls(mapping=((k, v) for k, v in zip(keys, [v for i in range(len(keys))])))

    def _mutate_key(self, k):
        return self.mutator(k)

    def _mutate_args(self, mapping=(), **kwargs):
        return ((self._mutate_key(k), v) for k, v in chain(mapping if not isinstance(mapping, Mapping) else mapping.items(), kwargs.items()))

    def __init__(self, mutator=lambda k: K, mapping=(), **kwargs):
        self.mutator = mutator
        super(MutatedDict, self).__init__(self._mutate_args(mapping, **kwargs))

    def __getitem__(self, k):
        return super(MutatedDict, self).__getitem__(self._mutate_key(k))
    
    def __setitem__(self, k, v):
        return super(MutatedDict, self).__setitem__(self._mutate_key(k), v)
    
    def __delitem__(self, k):
        return super(MutatedDict, self).__delitem__(self._mutate_key(k))
    
    def get(self, k, default=None):
        return super(MutatedDict, self).get(self._mutate_key(k), default)
    
    def setdefault(self, k, default=None):
        return super(MutatedDict, self).setdefault(self._mutate_key(k), default)
    
    def pop(self, k):
        return super(MutatedDict, self).pop(self._mutate_key(k), v)
    
    def update(self, mapping=(), **kwargs):
        super(MutatedDict, self).update(self._mutate_args(mapping, **kwargs))
    
    def __contains__(self, k):
        return super(MutatedDict, self).__contains__(self._mutate_key(k))
    
    def copy(self):
        return type(self)(self)
    
class CaseInsensitiveDict(MutatedDict):

    def __init__(self, mapping=(), **kwargs):
        super(CaseInsensitiveDict, self).__init__(mutator=str.lower, mapping=mapping, **kwargs)


