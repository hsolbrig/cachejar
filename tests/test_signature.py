# Copyright (c) 2017, Mayo Clinic
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#     Neither the name of the Mayo Clinic nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
import os
import unittest

import time
import urllib.error

from cachejar.signature import signature


class SignatureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = "http://hl7.org/fhir/w5.ttl"
        cls.url2 = "http://hl7.org/fhir/fhir.ttl"
        cls.file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'sig_file'))

    def test_sigs(self):
        if os.path.exists(self.file):
            os.remove(self.file)
        sig = signature(self.url)
        self.assertIsNotNone(sig)
        self.assertEqual(sig, signature(self.url))
        sig2 = signature(self.url2)
        self.assertIsNotNone(sig2)
        self.assertNotEqual(sig, sig2)
        with self.assertRaises(urllib.error.HTTPError):
            signature(self.url + 'z')
        with self.assertRaises(FileNotFoundError):
            signature(self.file)
        with open(self.file, 'w') as f:
            f.write("test")
        sig = signature(self.file)
        self.assertIsNotNone(sig)
        time.sleep(1)
        with open(self.file, 'a') as f:
            f.write("a")
        sig2 = signature(self.file)
        self.assertNotEqual(sig, sig2)
        os.remove(self.file)


if __name__ == '__main__':
    unittest.main()
