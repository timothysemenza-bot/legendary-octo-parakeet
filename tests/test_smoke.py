import unittest
from pathlib import Path


class TestSkeleton(unittest.TestCase):
    def test_expected_files_exist(self):
        self.assertTrue(Path("mod/main.lua").exists())
        self.assertTrue(Path("tools/validate_mod.py").exists())


if __name__ == "__main__":
    unittest.main()
