import subprocess

from destral.utils import detect_module
from destral.openerp import OpenERPService


def main():
    paths = subprocess.check_output([
        "git", "diff", "--name-only", "HEAD~1..HEAD"
    ])
    paths = [x for x in paths.split('\n') if x]
    modules_to_test = []
    for path in paths:
        module = detect_module(path)
        if module and module not in modules_to_test:
            modules_to_test.append(module)

    for module in modules_to_test:
        o = OpenERPService()
        db_name = o.create_database()
        o.db_name = db_name
        o.install_module(module)

if __name__ == '__main__':
    main()