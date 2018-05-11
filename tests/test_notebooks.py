import hashlib
import os
import unittest
import urllib.request
from contextlib import redirect_stdout
from io import StringIO

import cachejar


class ByteSum:
    # An MD5 summary of a URL
    def __init__(self, url):
        self.hash = hashlib.md5(urllib.request.urlopen(url).read()).hexdigest()


class MyClass:
    def __init__(self, fname: str, forward: bool):
        self.fname = fname if forward else fname[::-1]


class NotebookTestCase(unittest.TestCase):
    """
    Test of the code that appears in the notebook files
    """
    appid = os.path.basename(__file__).rsplit('.')[0]
    url = "http://hl7.org/fhir/fhir.ttl"

    def setUp(self):
        cachejar.jar(self.appid).clear()

    def test_example(self):
        appid = 'example_notebbook'
        url = "http://hl7.org/fhir/fhir.ttl"

        # Connect to the cachejar for this application
        jar = cachejar.jar(appid)

        # Remove any existing data
        jar.clear()

        # Invoke the same operation twice
        outf = StringIO()
        with redirect_stdout(outf):
            for _ in range(1, 3):
                obj = jar.object_for(url, ByteSum)
                if obj:
                    print("Retrived from cache")
                else:
                    print("Not cached - computing md5")
                    obj = ByteSum(url)
                    jar.update(url, obj, ByteSum)
                print(f"MD5 for {url} = {obj.hash}")
        self.assertEqual("""Not cached - computing md5
MD5 for http://hl7.org/fhir/fhir.ttl = 8ce6c3545b7a238f0091abe05dbcb7dd
Retrived from cache
MD5 for http://hl7.org/fhir/fhir.ttl = 8ce6c3545b7a238f0091abe05dbcb7dd
""", outf.getvalue())

    def testdocumentation(self):
        __version__ = "1.3.0"
        appid = __name__ + __version__
        cachejar.factory.clear(appid)

        def process_input(fname: str, forward: bool) -> MyClass:
            my_obj = cachejar.jar(appid).object_for(fname, MyClass, forward)
            if not my_obj:
                print(f"Processing {fname}")
                my_obj = MyClass(fname, forward)
                cachejar.jar(appid).update(fname, MyClass(fname, forward), MyClass, forward)
            else:
                print(f"Using cached image for {fname}")
            return my_obj

        outf = StringIO()
        with redirect_stdout(outf):
            print(process_input("https://github.com/hsolbrig/cachejar", forward=True).fname)
            print(process_input("https://github.com/hsolbrig/cachejar", forward=True).fname)
            print(process_input("https://github.com/hsolbrig/cachejar", forward=False).fname)
            print(process_input("https://github.com/hsolbrig/cachejar", forward=False).fname)
        self.assertEqual("""Processing https://github.com/hsolbrig/cachejar
https://github.com/hsolbrig/cachejar
Using cached image for https://github.com/hsolbrig/cachejar
https://github.com/hsolbrig/cachejar
Processing https://github.com/hsolbrig/cachejar
rajehcac/girblosh/moc.buhtig//:sptth
Using cached image for https://github.com/hsolbrig/cachejar
rajehcac/girblosh/moc.buhtig//:sptth
""", outf.getvalue())

        from cachejar.jar import CacheFactory
        outf = StringIO()
        with redirect_stdout(outf):
            print(cachejar.factory.cache_root)
            _ = cachejar.jar('someapp')  # Create a local cache
            print(cachejar.factory.cache_directory('someapp'))

            local_factory = CacheFactory('/tmp/caches')
            print(local_factory.cache_root)
            _ = local_factory.cachejar('someapp')
            print(local_factory.cache_directory('someapp'))
            # You can do this, but once done it holds for the life of the application (and Jupyter has
            # a life that extends well beyond this cell)
            # cachejar.factory = local_factory
        self.assertEqual("""/Users/mrf7578/.cachejar
/Users/mrf7578/.cachejar/someapp
/tmp/caches
/tmp/caches/someapp
""", outf.getvalue())
        outf = StringIO()
        with redirect_stdout(outf):
            print(cachejar.factory.cache_directory('someapp'))
            cachejar.factory.clear('someapp')                           # Remove all contents
            print(cachejar.factory.cache_directory('someapp'))
            cachejar.factory.clear('someapp', remove_completely=True)  # Remove all knowledge
            print(cachejar.factory.cache_directory('someapp'))
        self.assertEqual("""/Users/mrf7578/.cachejar/someapp
/Users/mrf7578/.cachejar/someapp
None
""", outf.getvalue())

    def test_disabled(self):
        outf = StringIO()
        with redirect_stdout(outf):
            jar = cachejar.jar('someapp')
            print(f"Factory: {cachejar.factory.disabled}")
            print(f"Jar: {jar.disabled}\n")

            cachejar.factory.disabled = True
            print(f"Factory: {cachejar.factory.disabled}")
            print(f"Jar: {jar.disabled}\n")

            jar.disabled = True
            print(f"Factory: {cachejar.factory.disabled}")
            print(f"Jar: {jar.disabled}\n")

            cachejar.factory.disabled = False
            print(f"Factory: {cachejar.factory.disabled}")
            print(f"Jar: {jar.disabled}\n")
        self.assertEqual("""Factory: False
Jar: False

Factory: True
Jar: True

Factory: True
Jar: True

Factory: False
Jar: True

""", outf.getvalue())


if __name__ == '__main__':
    unittest.main()
