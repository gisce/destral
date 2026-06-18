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


class SortModulesByDependenciesTests(unittest.TestCase):

    def setUp(self):
        """Create a temporary addons directory with test modules"""
        self.addons_dir = tempfile.mkdtemp()
        
        # Create module structure:
        # base (no deps)
        # module_a depends on base
        # module_b depends on module_a, base
        # module_c depends on module_b, module_a, base
        
        modules_config = {
            'base': [],
            'module_a': ['base'],
            'module_b': ['module_a', 'base'],
            'module_c': ['module_b', 'module_a', 'base']
        }
        
        for module_name, deps in modules_config.items():
            module_dir = os.path.join(self.addons_dir, module_name)
            os.makedirs(module_dir)
            terp_file = os.path.join(module_dir, '__terp__.py')
            with open(terp_file, 'w') as f:
                f.write("{\n")
                f.write("    'name': '{}',\n".format(module_name))
                f.write("    'depends': {}\n".format(deps))
                f.write("}\n")

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.addons_dir)

    def test_sort_single_module(self):
        """Test sorting with a single module"""
        result = utils.sort_modules_by_dependencies(['base'], self.addons_dir)
        self.assertEqual(result, ['base'])

    def test_sort_two_modules_with_dependency(self):
        """Test module_a depends on base, should return [base, module_a]"""
        result = utils.sort_modules_by_dependencies(
            ['module_a', 'base'], self.addons_dir
        )
        self.assertEqual(result, ['base', 'module_a'])

    def test_sort_two_modules_with_dependency_reversed_input(self):
        """Test with reversed input order"""
        result = utils.sort_modules_by_dependencies(
            ['base', 'module_a'], self.addons_dir
        )
        self.assertEqual(result, ['base', 'module_a'])

    def test_sort_multiple_modules_linear_dependencies(self):
        """Test module_c -> module_b -> module_a -> base"""
        result = utils.sort_modules_by_dependencies(
            ['module_c', 'module_a', 'base'], self.addons_dir
        )
        # base should come first, then module_a, then module_c
        # module_c depends on module_a and base
        self.assertLess(result.index('base'), result.index('module_a'))
        self.assertLess(result.index('module_a'), result.index('module_c'))

    def test_sort_all_modules(self):
        """Test sorting all modules respects dependency chain"""
        result = utils.sort_modules_by_dependencies(
            ['module_c', 'module_b', 'module_a', 'base'], self.addons_dir
        )
        # Verify dependency order
        self.assertLess(result.index('base'), result.index('module_a'))
        self.assertLess(result.index('module_a'), result.index('module_b'))
        self.assertLess(result.index('module_b'), result.index('module_c'))

    def test_sort_modules_out_of_order(self):
        """Test with modules provided in random order"""
        result = utils.sort_modules_by_dependencies(
            ['module_b', 'base', 'module_c', 'module_a'], self.addons_dir
        )
        # Verify dependency order
        self.assertLess(result.index('base'), result.index('module_a'))
        self.assertLess(result.index('module_a'), result.index('module_b'))
        self.assertLess(result.index('module_b'), result.index('module_c'))

    def test_sort_empty_list(self):
        """Test with empty list"""
        result = utils.sort_modules_by_dependencies([], self.addons_dir)
        self.assertEqual(result, [])

    def test_sort_modules_without_shared_dependencies(self):
        """Test sorting modules that don't depend on each other"""
        # Only include module_a and base (module_a depends on base)
        result = utils.sort_modules_by_dependencies(
            ['module_a', 'base'], self.addons_dir
        )
        self.assertEqual(result, ['base', 'module_a'])


if __name__ == '__main__':
    unittest.main()
