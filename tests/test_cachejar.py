import os
import unittest
from pathlib import Path

import cachejar
from tests.utils.make_and_clear_directory import make_and_clear_directory


class TestObj:
    def __init__(self, s: str="penguin", v: int=42):
        self.s = s
        self.v = v

    def __eq__(self, other):
        return self.s == other.s and self.v == other.v

    def __repr__(self) -> str:
        return self.s + ":" + str(self.v)


class CacheJarTestCase(unittest.TestCase):
    datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    datafilename = os.path.join(datadir, 'datafile')
    datafilename2 = os.path.join(datadir, 'datafile2')
    appid = __name__
    appid2 = os.path.basename(__file__)

    def setUp(self):
        cachejar.factory.clear(self.appid, remove_completely=True)
        cachejar.factory.clear(self.appid2, remove_completely=True)

    def tearDown(self):
        cachejar.factory.clear(self.appid, remove_completely=True)
        cachejar.factory.clear(self.appid2, remove_completely=True)

    def num_data_files(self) -> int:
        return len([f for f in os.listdir(cachejar.factory.cache_directory(self.appid)) if f != 'index'])

    def test_pickled_file(self):
        """ Basic functional tests """
        
        o1 = TestObj()
        # Reference the cachejar
        jar = cachejar.jar(self.appid)
        
        # Add the same object to the jar twice
        jar.update(self.datafilename, o1, TestObj)
        cachejar.jar(self.appid).update(self.datafilename, o1, TestObj)
        self.assertEqual(1, self.num_data_files())
        
        # Pull the object out of the jar
        o2 = jar.object_for(self.datafilename, TestObj)
        self.assertIsNotNone(o2)
        self.assertEqual(o1, o2)
        
        # Change the data file signature
        Path(self.datafilename).touch()
        self.assertIsNone(jar.object_for(self.datafilename, TestObj))
        # The chaange in signature will flush the cache
        self.assertEqual(0, self.num_data_files())

        # Create an object with 'dependent' parameters
        o1 = TestObj('baseball', 17)
        jar.update(self.datafilename, o1, TestObj, 'baseball', 17)
        o2 = jar.object_for(self.datafilename, TestObj, 'baseball', 17)
        self.assertEqual(o1, o2)
        self.assertEqual(1, self.num_data_files())
        
        # Create a second object with different parameters
        self.assertIsNone(jar.object_for(self.datafilename, TestObj, 'robin', -173))
        o3 = TestObj('robin', -173)
        
        # Add same parameters, two different data files
        jar.update(self.datafilename, o3, TestObj, 'robin', -173)
        jar.update(self.datafilename2, o3, TestObj, 'robin', -173)
        o4 = jar.object_for(self.datafilename2, TestObj, 'robin', -173)
        self.assertEqual(o3, o4)
        self.assertEqual(3, self.num_data_files())
        
        # Clean everything for a single file, and obj id
        jar.clean(self.datafilename, TestObj, 'robin', -173)
        self.assertEqual(2, self.num_data_files())
        
        # Clean everything for a whole file
        jar.clean(self.datafilename)
        self.assertEqual(1, self.num_data_files())
        
        # Clean everything
        jar.clean()
        self.assertEqual(0, self.num_data_files())
        
    def test_multi_applications(self):
        """ Make sure that multi applications can use the same cache """
        o1 = TestObj("a", 1)
        o2 = TestObj("b", 2)
        cachejar.jar(self.appid).update(self.datafilename, o1, TestObj)
        cachejar.jar(self.appid2).update(self.datafilename, o2, TestObj)
        self.assertEqual(1, self.num_data_files())
        o3 = cachejar.jar(self.appid).object_for(self.datafilename, TestObj)
        o4 = cachejar.jar(self.appid2).object_for(self.datafilename, TestObj)
        self.assertEqual(o1, o3)
        self.assertEqual(o2, o4)
        
    def test_singleton(self):
        """ Make sure identity is preserved across imports """
        from cachejar import factory as fact2
        cachejar.jar(self.appid).update(self.datafilename, TestObj(), TestObj, "DUPTEST")
        o = fact2.cachejar(self.appid).object_for(self.datafilename, TestObj, "DUPTEST")
        self.assertIsNotNone(o)
        self.assertEqual("penguin", o.s)

    def test_cache_loc(self):
        """ Change the default cache location """
        from cachejar.jar import CacheFactory

        test_dir = os.path.join(self.datadir, 'cache')
        make_and_clear_directory(test_dir)
        local_factory = CacheFactory(test_dir)
        jar = local_factory.cachejar(self.appid)

        o1 = TestObj()
        o1.foo = "bagels"
        jar.update(self.datafilename, o1, TestObj)
        o2 = TestObj()
        o2.foo = "cheese"
        jar.update(self.datafilename2, o2, TestObj)
        ot1 = jar.object_for(self.datafilename, TestObj)
        ot2 = jar.object_for(self.datafilename2, TestObj)
        self.assertEqual(o1, ot1)
        self.assertEqual(o2, ot2)
        self.assertIsNone(cachejar.jar(self.appid).object_for(self.datafilename, TestObj))
        self.assertIsNone(cachejar.jar(self.appid).object_for(self.datafilename2, TestObj))
        local_factory.clear(self.appid, remove_completely=True)
        cachejar.factory.clear(self.appid, remove_completely=True)

    def test_urls(self):
        """ Test application against URLs """
        solid_url = "http://hl7.org/fhir/fhir.ttl"
        o1 = TestObj()
        o1.url = solid_url
        changing_url = "https://www.nytimes.com/"
        o2 = TestObj()
        o2.url = changing_url
        cachejar.factory.clear(self.appid)
        jar = cachejar.jar(self.appid)
        jar.update(solid_url, o1, TestObj)
        jar.update(changing_url, o2, TestObj)
        ot1 = jar.object_for(solid_url, TestObj)
        self.assertIsNotNone(ot1)
        # Note: this doesn't really test what we think.  We need to find a URL somewhere whose update data
        # continuously changes
        ot2 = jar.object_for(changing_url+'z', TestObj)
        self.assertIsNone(ot2)

    def test_foreign_file(self):
        """ Make sure the cleanup function recognizes muddling with the directory """
        from cachejar.jar import CacheFactory, CacheError
        appid = 'test_foreign_file'
        test_dir = os.path.join(self.datadir, 'cache')
        make_and_clear_directory(test_dir)

        local_factory = CacheFactory(test_dir)
        jar = local_factory.cachejar(appid)
        o = TestObj()
        jar.update(self.datafilename, o, TestObj)
        foreign_fname = os.path.join(test_dir, appid, 'foo')
        with open(foreign_fname, 'w') as f:
            f.write("I'm foreign")
        with self.assertRaises(CacheError):
            local_factory.clear(appid, remove_completely=True)
        os.remove(foreign_fname)
        local_factory.clear(appid, remove_completely=True)
        self.assertFalse(os._exists(os.path.join(test_dir, appid)))

    def test_damaged_index(self):
        """ Make sure we know what happens when the index isn't right """
        from cachejar.jar import CacheFactory, CacheError

        appid = 'test_damaged_index'
        test_dir = os.path.join(self.datadir, 'cache')
        make_and_clear_directory(test_dir)
        local_factory = CacheFactory(test_dir)
        jar = local_factory.cachejar(appid)
        o = TestObj()
        jar.update(self.datafilename, o, TestObj)
        with open(jar._cache_directory_index, 'a') as f:
            f.write("dirt")
        with self.assertRaises(CacheError):
            CacheFactory(test_dir)
        make_and_clear_directory(test_dir)

    def test_reload_file(self):
        """ Make sure that saving and restoring the index behaves correctly.  JSON doesn't deal well with tuples... """
        o1 = TestObj()
        # Reference the cachejar
        jar = cachejar.jar(self.appid)

        # Add the same object to the jar twice
        jar.update(self.datafilename, o1, TestObj)
        o2 = jar.object_for(self.datafilename, TestObj)
        self.assertEqual(o1, o2)
        jar._load_index()
        o3 = jar.object_for(self.datafilename, TestObj)
        self.assertEqual(o1, o3)

    def test_basic_clear(self):
        """ Catch a bit of code that wasn't caught elsewhere """
        o1 = TestObj()
        jar = cachejar.jar(self.appid)
        jar.update(self.datafilename, o1, TestObj)
        cachejar.jar(self.appid).clear()

    def test_kw_parms(self):
        o1 = TestObj('abc', 123)
        o2 = TestObj('def', 456)
        o3 = TestObj('ghi', 789)
        jar = cachejar.jar(self.appid)
        jar.update(self.datafilename, o1, TestObj, 'abc', 123, test=False)
        jar.update(self.datafilename, o2, TestObj, 'abc', 123, test=True)
        jar.update(self.datafilename, o3, TestObj, 'abc', test=True)
        ot1 = jar.object_for(self.datafilename, TestObj, 'abc', 123, test=False)
        ot2 = jar.object_for(self.datafilename, TestObj, 'abc', 123, test=True)
        ot3 = jar.object_for(self.datafilename, TestObj, 'abc', test=True)
        self.assertEqual(o1, ot1)
        self.assertEqual(o2, ot2)
        self.assertEqual(o3, ot3)


if __name__ == '__main__':
    unittest.main()
