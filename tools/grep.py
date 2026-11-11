"""A tool that searches files for lines matching a regular expression, like grep."""

import glob
import os
import re

from tools.utils import is_path_safe


def grep(regex, path):
    r"""Return every line matching the regex in the files matching the glob path.

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.mkdtemp()
    >>> os.chdir(tmp)
    >>> _ = open('a.py', 'w').write('x = 1\n# TODO: fix x\ny = 2\n')
    >>> _ = open('b.py', 'w').write('# TODO: add tests\nprint(y)\n')
    >>> grep('TODO', 'a.py')
    '# TODO: fix x'
    >>> grep('TODO', '*.py')
    '# TODO: fix x\n# TODO: add tests'
    >>> grep(r'^[xy] = \d', '*.py')
    'x = 1\ny = 2'
    >>> grep('nothing here', '*.py')
    ''
    >>> grep('TODO', 'missing.py')
    ''
    >>> _ = open('pic.png', 'wb').write(b'\x89PNG\xff\xfe\x80TODO')
    >>> os.mkdir('sub')
    >>> grep('TODO', '*')
    '# TODO: fix x\n# TODO: add tests'
    >>> grep('(unclosed', '*.py')
    'Error: invalid regex (unclosed'
    >>> grep('root', '/etc/passwd')
    'Error: unsafe path'
    >>> grep('TODO', '../*.py')
    'Error: unsafe path'
    >>> os.chdir(old)
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    try:
        pattern = re.compile(regex)
    except re.error:
        return f'Error: invalid regex {regex}'
    matches = []
    for filename in sorted(glob.glob(path)):
        if not os.path.isfile(filename):
            continue
        try:
            with open(filename, encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            if pattern.search(line):
                matches.append(line)
    return '\n'.join(matches)
