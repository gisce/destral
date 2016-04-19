# coding=utf-8
import os

from destral.utils import *
from expects import *


_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_fixture(*args):
    return os.path.join(_ROOT, 'fixtures', *args)


with description('With a diff'):
    with it('has to get the files modified'):
        with open(get_fixture('test.diff'), 'r') as diff_file:
            diff_text = diff_file.read()

        paths = find_files(diff_text)
        expect(paths).to(contain_only(
            'oorq/decorators.py',
            'oorq/oorq.py',
            'oorq/tests/test_oorq/partner.py',
            'requirements.txt',
            'addons/foo/bar.txt'
        ))
