# coding=utf-8
import logging

from pylint.reporters.text import ColorizedTextReporter
from pylint.lint import PyLinter
from pylint.config import find_pylintrc


logger = logging.getLogger(__name__)


def run_linter(files=None):
    if files is None:
        return
    logger.info('Linting {}'.format(', '.join(files)))
    rep = ColorizedTextReporter()
    linter = PyLinter(reporter=rep, pylintrc=find_pylintrc())
    linter.load_default_plugins()
    linter.disable('I')
    linter.enable('c-extension-no-member')
    linter.read_config_file()
    linter.load_config_file()
    linter.check(files)
    linter.generate_reports()
