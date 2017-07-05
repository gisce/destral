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
        with it('must return empty lists when the POT and PO files have'
                ' the same msg id and string'):
            pathA = get_fixture('potfileA.pot')
            pathB = get_fixture('pofileA.po')
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathB)
            expect(untranslated_msg).to(equal([]))
            expect(missing_msg).to(equal([]))
        with it('must return a tuple with the missing and untranslated strings'
                ' when the PO files have 2 missing strings and 1 untranslated'):
            pathA = get_fixture('potfileA.pot')
            pathC = get_fixture('potfileB.pot')  # Has 2 less messages than A
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathC)
            expect(missing_msg).to(equal([
                "One String", "A Larger string!!!!"
            ]))
            expect(untranslated_msg).to(equal([(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Suspendisse posuere iaculis mauris. Aliquam ornare ante lectus,"
                "nec feugiat nunc dignissim in."
            )]))
        with it('must return an empty list for the missing strings and a list'
                ' with the untranslated string when the POT and PO files have'
                ' 1 missing translation'):
            pathA = get_fixture('potfileA.pot')
            pathC = get_fixture('pofileB.po')  # Has 1 message untranslated
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathC)
            expect(missing_msg).to(equal([]))
            expect(untranslated_msg).to(equal([(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Suspendisse posuere iaculis mauris. Aliquam ornare ante lectus,"
                "nec feugiat nunc dignissim in."
            )]))
        with it('must return booleans (False) for both lists when any of the'
                ' POT files cannot be found'):
            pathA = get_fixture('potfileA.pot')
            pathD = get_fixture('potfileC.pot')  # Does not exist
            missing_msg, untranslated_msg = compare_pofiles(pathA, pathD)
            expect(untranslated_msg).to(be_none)
            expect(missing_msg).to(be_none)
            # invert POT positions
            missing_msg, untranslated_msg = compare_pofiles(pathD, pathA)
            expect(untranslated_msg).to(be_none)
            expect(missing_msg).to(be_none)
