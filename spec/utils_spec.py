# coding=utf-8
from __future__ import absolute_import


from destral.utils import find_files, compare_pofiles
from expects import *

from .fixtures import get_fixture



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

with description('Translations'):
    with context('Comparing pofiles'):
        with it('Compare the POT and PO files with the same msg id and string'):
            pathA = get_fixture('potfileA.pot')
            pathB = get_fixture('pofileA.po')
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathB)
            expect(untranslated_msg).to(equal(0))
            expect(missing_msg).to(equal(0))
        with it('Compare PO files with one PO missing'
                ' 2 strings and 1 untranslated'):
            pathA = get_fixture('potfileA.pot')
            pathC = get_fixture('potfileB.pot')  # Has 2 less messages than A
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathC)
            expect(untranslated_msg).to(equal(1))
            expect(missing_msg).to(equal(2))
        with it('Compare POT and PO files missing 1 translation'):
            pathA = get_fixture('potfileA.pot')
            pathC = get_fixture('pofileB.po')  # Has 1 message untranslated
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathC)
            expect(missing_msg).to(equal(0))
            expect(untranslated_msg).to(equal(1))
        with it('Compare POT files with one missing POT file'):
            pathA = get_fixture('potfileA.pot')
            pathD = get_fixture('potfileC.pot')  # Does not exist
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathD)
            expect(untranslated_msg).to(equal(-1))
            expect(missing_msg).to(equal(-1))
