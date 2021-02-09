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

import ldap, ldap.sasl, ldap.schema
import os
import tempfile
from subprocess import Popen, PIPE
import threading
from enum import Enum
import atexit
import hashlib
import urllib

RESULT_KEY_DN = 'dn'
RESULT_KEY_ATTRIBUTES = 'attributes'

class SaslMechanism(Enum):
    GSSAPI = 1
    DIGEST_MD5 = 2

class SaslBindingContext:

    __ticket_dict__ = {}

    def get_tgt_path(userId, password):
        # dictionary of temp file keyed by unique cred combos
        d = SaslBindingContext.__ticket_dict__
        hash = hashlib.md5("{}\0{}".format(urllib.parse.quote(userId), urllib.parse.quote(password)).encode('utf-8')).hexdigest()
        if not hash in d:
            if not hash in d:
                d[hash] = tempfile.NamedTemporaryFile()
        return d[hash].name

    def __init__(self, url, userId, password, sasl_mechanism=SaslMechanism.GSSAPI, chase_referrals=False, min_ssf=56, trace_level=0):
        self.ldap = None
        self.url = url
        self.userId = userId
        self.password = password
        self.sasl_mechanism = sasl_mechanism
        self.chase_referrals = chase_referrals
        self.min_ssf = min_ssf
        self.trace_level = trace_level

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        if self.ldap:
            self.close()
        self.ldap = ldap.initialize(self.url, trace_level=self.trace_level)
        self.ldap.set_option(ldap.OPT_REFERRALS, 1 if self.chase_referrals else 0)
        self.ldap.set_option(ldap.OPT_X_SASL_SSF_MIN, self.min_ssf)
        self.ldap.set_option(ldap.OPT_X_SASL_NOCANON, 1)
        if self.sasl_mechanism == SaslMechanism.GSSAPI:
            sasl_auth = ldap.sasl.sasl({}, 'GSSAPI')
            with threading.Lock():
                f = SaslBindingContext.get_tgt_path(self.userId, self.password)
                os.environ['KRB5CCNAME'] = f
                # test TGT with klist - zero exit code means valid
                klist = Popen(['/usr/bin/klist', '-s'])
                if klist.wait() != 0:
                    kinit = Popen(['/usr/bin/kinit', self.userId], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    outs, errs = kinit.communicate(input=b'%s\n' % self.password.encode('UTF-8'))
                    if errs:
                        raise Exception(errs)
                self.ldap.sasl_interactive_bind_s("", sasl_auth)
        elif self.sasl_mechanism == SaslMechanism.DIGEST_MD5:
            sasl_auth = ldap.sasl.sasl({
                ldap.sasl.CB_AUTHNAME: self.userId,
                ldap.sasl.CB_PASS: self.password,
            }, 'DIGEST-MD5')
            self.ldap.sasl_interactive_bind_s("", sasl_auth)
        else:
            raise Exception('Unsupported mechanism: %s' % self.sasl_mechanism)

    def close(self):
        if self.ldap:
            self.ldap.unbind_s()
            self.ldap = None

    def search(self, base, scope=ldap.SCOPE_SUBTREE, filter='(objectClass=*)', attributes=None, referrals=False, attrsonly=False):
        if not self.ldap:
            self.open()
        results = self.ldap.search_s(base, scope, filterstr=filter, attrlist=attributes, attrsonly=1 if attrsonly else 0)
        if results:
            # results are tuples of (dn, attrs) except referrals (last 3?) with null dn
            return [{RESULT_KEY_DN: x[0], RESULT_KEY_ATTRIBUTES:x[1]} for x in results if referrals or x[0]]
        else:
            return []

    def delete(self, dn):
        if not self.ldap:
            self.open()
        self.ldap.delete_s(dn)

    def add(self, dn, modlist):
        if not self.ldap:
            self.open()
        self.ldap.add_s(dn, modlist)

    def modify(self, dn, modlist):
        if not self.ldap:
            self.open()
        self.ldap.modify_s(dn, modlist)

    def rename(self, dn, rdn):
        if not self.ldap:
            self.open()
        self.ldap.rename_s(dn, rdn)

