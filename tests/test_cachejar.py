import os
import unittest
from pathlib import Path

from cachejar import factory
from cachejar.jar import CacheFactory, CacheError
from tests.utils.make_and_clear_directory import make_and_clear_directory


class TestObj:
    def __init__(self):
        self.cls = "CLASS"
        self.val = 42


class CacheJarTestCase(unittest.TestCase):
    default_cache_directory = None
    datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    datafilename = os.path.join(datadir, 'datafile')
    datafilename2 = os.path.join(datadir, 'datafile2')
    appid = None

    @classmethod
    def setUpClass(cls):
        cls.default_cache_directory = factory.cache_directory
        cls.appid = cls.__name__
        factory.clear(cls.appid, remove_completely=True)
        factory.cachejar(cls.appid).update(cls.datafilename, TestObj(), TestObj)

    @classmethod
    def tearDownClass(cls):
        factory.clear(cls.appid, remove_completely=True)

    def setUp(self):
        # Recover if there is an error when we're not working with the default
        factory.cache_directory = self.default_cache_directory

    def num_data_files(self) -> int:
        return len([f for f in os.listdir(factory.cache_directory(self.appid)) if f != 'index'])

    def test_pickled_file(self):
        o1 = TestObj()
        jar = factory.cachejar(self.appid)
        jar.update(self.datafilename, o1, TestObj)
        jar.update(self.datafilename, o1, TestObj)
        o2 = jar.object_for(self.datafilename, TestObj)
        self.assertIsNotNone(o2)
        self.assertEqual(o1.val, o2.val)
        Path(self.datafilename).touch()
        self.assertIsNone(jar.object_for(self.datafilename, TestObj))
        o1.val = 173
        jar.update(self.datafilename, o1, TestObj)
        o2 = jar.object_for(self.datafilename, TestObj)
        self.assertEqual(173, o2.val)
        self.assertEqual(2, self.num_data_files())
        jar.clean(name_or_url=self.datafilename)
        self.assertEqual(1, self.num_data_files())

    def test_singleton(self):
        o = factory.cachejar(self.appid).object_for(self.datafilename, TestObj)
        self.assertIsNotNone(o)
        self.assertEqual("CLASS", o.cls)

    def test_cache_loc(self):
        appid = 'test_cache_loc'
        test_dir = os.path.join(self.datadir, 'cache')
        make_and_clear_directory(test_dir)
        local_factory = CacheFactory(test_dir)
        jar = local_factory.cachejar(appid)

        o1 = TestObj()
        o1.foo = "bagels"
        jar.update(self.datafilename, o1, TestObj)
        o2 = TestObj()
        o2.foo = "cheese"
        jar.update(self.datafilename2, o2, TestObj)
        ot1 = jar.object_for(self.datafilename, TestObj)
        ot2 = jar.object_for(self.datafilename2, TestObj)
        self.assertEqual("bagels", ot1.foo)
        self.assertEqual("cheese", ot2.foo)
        self.assertIsNone(factory.cachejar(appid).object_for(self.datafilename, TestObj))
        self.assertIsNone(factory.cachejar(appid).object_for(self.datafilename2, TestObj))
        local_factory.clear(appid, remove_completely=True)

    def test_urls(self):
        solid_url = "http://hl7.org/fhir/fhir.ttl"
        o1 = TestObj()
        o1.url = solid_url
        changing_url = "https://www.nytimes.com/"
        o2 = TestObj()
        o2.url = changing_url
        factory.clear(self.appid)
        jar = factory.cachejar(self.appid)
        jar.update(solid_url, o1, TestObj)
        jar.update(changing_url, o2, TestObj)
        ot1 = jar.object_for(solid_url, TestObj)
        self.assertIsNotNone(ot1)
        # Note: this doesn't really test what we think.  We need to find a URL somewhere whose update data
        # continuously changes
        ot2 = jar.object_for(changing_url+'z', TestObj)
        self.assertIsNone(ot2)

    def test_foreign_file(self):
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
            local_factory = CacheFactory(test_dir)
        make_and_clear_directory(test_dir)


if __name__ == '__main__':
    unittest.main()
