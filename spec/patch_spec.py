from expects import *


with description('Wrapping Cursor object'):
    with it('must return True on commit, rollback and close'):
        from destral.patch import PatchedCursor

        class MockCursor(object):
            def execute(self, sql):
                return 'execute', sql

        p = PatchedCursor(MockCursor())

        expect(p.commit()).to(be_true)
        expect(p.rollback()).to(be_true)
        expect(p.close()).to(be_true)

        expect(p.execute('select 1')).to(equal(('execute', 'select 1')))
