import unittest

from cachejar.signature import signature
from tests.utils.file_utils import FileTesting


class DirectorySignatureTestCase(FileTesting):
    def setUp(self):
        self.last_sig = ''
        super().setUp()
    
    def changed(self):
        self.assertNotEqual(self.last_sig, signature(self.test_dir))
        self.last_sig = signature(self.test_dir)        # Recalc just to be sure
        
    def unchanged(self):
        self.assertEqual(self.last_sig, signature(self.test_dir))
    
    def do_eval(self, subdir: str) -> None:
        prefix = 's' if subdir else ''
        self.add_file(prefix + "data1.txt", subdir)
        self.changed()
        self.add_file(prefix + "data2.txt", subdir)
        self.changed()
        self.modify_file(prefix + "data1.txt", subdir)
        self.changed()
        self.touch_file(prefix + "data2.txt", subdir)
        self.changed()
        self.del_file(prefix + "data2.txt", subdir)
        self.changed()
        self.unchanged()
        
    def test_directory_signatue(self):
        self.changed()
        self.unchanged()
        self.do_eval('')
        self.make_subdir('subdir')
        self.do_eval('subdir')
        self.rm_subdir('subdir')
        self.do_eval('')


if __name__ == '__main__':
    unittest.main()
