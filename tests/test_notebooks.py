import hashlib
import os
import unittest
import urllib.request

import cachejar


class ByteSum:
    # An MD5 summary of a URL
    def __init__(self, url):
        self.hash = hashlib.md5(urllib.request.urlopen(url).read()).hexdigest()


class NotebookTestCase(unittest.TestCase):
    """
    Test of the code that appears in the notebook files
    """
    appid = os.path.basename(__file__).rsplit('.')[0]
    url = "http://hl7.org/fhir/fhir.ttl"

    def setUp(self):
        cachejar.jar(self.appid).clear()

    def test_basics(self):
        jar = cachejar.jar(self.appid)
        jar.clear()
        rslt1 = jar.object_for(self.url, ByteSum)
        self.assertIsNone(rslt1)
        rslt1 = ByteSum(self.url)
        jar.update(self.url, rslt1, ByteSum)
        rslt2 = jar.object_for(self.url, ByteSum)
        self.assertIsNotNone(rslt2)
        self.assertEqual(rslt1.hash, rslt2.hash)
        jar.clear()


if __name__ == '__main__':
    unittest.main()
