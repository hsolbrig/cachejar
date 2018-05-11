import os
import time
import unittest
from pathlib import Path
from typing import Optional

from tests.utils.make_and_clear_directory import make_and_clear_directory


class FileTesting(unittest.TestCase):
    test_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data', 'directory')

    def setUp(self):
        make_and_clear_directory(self.test_dir)

    def tearDown(self):
        make_and_clear_directory(self.test_dir)

    def add_file(self, fname: str, subdir: Optional[str] = '') -> None:
        with open(os.path.join(self.test_dir, subdir, fname), 'w') as f:
            f.write(fname)

    def modify_file(self, fname: str, subdir: Optional[str] = '') -> None:
        with open(os.path.join(self.test_dir, subdir, fname), 'a') as f:
            f.write('a')

    def touch_file(self, fname: str, subdir: Optional[str] = '') -> None:
        time.sleep(1)           # Touch has a coarse resolution
        Path(os.path.join(self.test_dir, subdir, fname)).touch()

    def del_file(self, fname: str, subdir: Optional[str] = '') -> None:
        os.remove(os.path.join(self.test_dir, subdir, fname))

    def make_subdir(self, subdir: str) -> None:
        make_and_clear_directory(os.path.join(self.test_dir, subdir))

    def rm_subdir(self, subdir: str) -> None:
        make_and_clear_directory(os.path.join(self.test_dir, subdir), remake=False)
