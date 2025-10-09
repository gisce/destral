# coding=utf-8
import os
import shutil
import tempfile
import unittest

from destral import utils


class UpdateConfigTests(unittest.TestCase):

    def test_update_config_merges_values_in_place(self):
        config = {'existing': 1}

        result = utils.update_config(config, added=2)

        self.assertTrue(result is config)
        self.assertEqual(result, {'existing': 1, 'added': 2})


class FindFilesTests(unittest.TestCase):

    def test_find_files_returns_unique_paths_from_diff(self):
        diff = (
            "--- a/foo/bar.py\n"
            "+++ b/foo/bar.py\n"
            "--- a/README\n"
            "+++ b/README\n"
        )

        paths = utils.find_files(diff)
        expected = ['foo/bar.py', 'README']
        self.assertEqual(sorted(paths), sorted(expected))


class CoverageModulesPathTests(unittest.TestCase):

    def test_generates_relative_real_paths(self):
        addons_dir = tempfile.mkdtemp()
        try:
            module_dir = os.path.join(addons_dir, 'mod_a')
            os.makedirs(module_dir)

            paths = utils.coverage_modules_path(['mod_a'], addons_dir)

            expected = os.path.relpath(os.path.realpath(module_dir))
            self.assertEqual(paths, [expected])
        finally:
            shutil.rmtree(addons_dir)


if __name__ == '__main__':
    unittest.main()
