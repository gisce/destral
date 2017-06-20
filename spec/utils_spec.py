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
        with it('must check all msg in first po file to be in the second one'):
            pathA = get_fixture('potfileA.pot')
            pathB = get_fixture('pofileA.po')    # Has all messages translated
            pathC = get_fixture('potfileB.pot')  # Has 2 less messages than A
            pathD = get_fixture('potfileC.pot')  # Does not exist
            missing_msg = compare_pofiles(pathA, pathB)
            expect(missing_msg).to(equal(0))
            missing_msg = compare_pofiles(pathA, pathC)
            expect(missing_msg).to(equal(2))
            missing_msg = compare_pofiles(pathA, pathD)
            expect(missing_msg).to(equal(-1))

        with it('must check all msg in first po file to be translated in '
                'the second one'):
            pathA = get_fixture('potfileA.pot')
            pathB = get_fixture('pofileA.po')  # Has all messages translated
            pathC = get_fixture('pofileB.po')  # Has 1 message untranslated
            pathD = get_fixture('pofileC.po')  # Does not exist
            untranslated_msg = compare_pofiles(pathA, pathB, True)
            expect(untranslated_msg).to(equal(0))
            untranslated_msg = compare_pofiles(pathA, pathC, True)
            expect(untranslated_msg).to(equal(1))
            untranslated_msg = compare_pofiles(pathA, pathD, True)
            expect(untranslated_msg).to(equal(-1))
