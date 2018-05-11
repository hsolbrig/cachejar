import unittest

import cachejar
from tests.utils.file_utils import FileTesting


class TestObj:
    obj_num: int = 1

    def __init__(self):
        self.objid = f"obj{TestObj.obj_num}"
        TestObj.obj_num += 1


class DirectoryCacheTestCase(FileTesting):
    appid = None

    @classmethod
    def setUpClass(cls):
        cls.appid = DirectoryCacheTestCase.__name__

    def setUp(self):
        super().setUp()
        self.jar = cachejar.jar(self.appid)

    def tearDown(self):
        self.jar.clear()
        super().tearDown()

    def uncached(self) -> None:
        self.assertIsNone(self.jar.object_for(self.test_dir, TestObj))
        self.jar.update(self.test_dir, TestObj(), TestObj)

    def cached(self) -> None:
        self.assertIsNotNone(self.jar.object_for(self.test_dir, TestObj))

    def do_eval(self, subdir: str) -> None:
        prefix = 's' if subdir else ''
        self.add_file(prefix+"data1.txt", subdir)
        self.uncached()
        self.add_file(prefix+"data2.txt", subdir)
        self.uncached()
        self.modify_file(prefix+"data1.txt", subdir)
        self.uncached()
        self.touch_file(prefix+"data2.txt", subdir)
        self.uncached()
        self.del_file(prefix+"data2.txt", subdir)
        self.uncached()
        self.cached()

    def test_directory_caching(self):
        self.uncached()
        self.cached()
        self.do_eval('')
        self.make_subdir('subdir')
        self.do_eval('subdir')
        self.rm_subdir('subdir')
        self.do_eval('')


if __name__ == '__main__':
    unittest.main()
