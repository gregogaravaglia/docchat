"""A tool that lists the files in a folder, like the shell's ls."""

import glob
import os

from tools.utils import is_path_safe


def ls(path='.'):
    """List the files in a folder (the current folder by default), sorted asciibetically.

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.mkdtemp()
    >>> os.chdir(tmp)
    >>> os.mkdir('docs')
    >>> for name in ['b.txt', 'a.txt', 'Z.md', 'docs/notes.txt', 'docs/plan.md']:
    ...     _ = open(name, 'w').write('hi')
    >>> ls()
    'Z.md  a.txt  b.txt  docs'
    >>> ls('')
    'Z.md  a.txt  b.txt  docs'
    >>> ls('.')
    'Z.md  a.txt  b.txt  docs'
    >>> ls('docs')
    'notes.txt  plan.md'
    >>> ls('docs/')
    'notes.txt  plan.md'
    >>> ls('a.txt')
    'a.txt'
    >>> ls('missing')
    "ls: cannot access 'missing': No such file or directory"
    >>> os.mkdir('empty')
    >>> ls('empty')
    ''
    >>> ls('/etc')
    'Error: unsafe path'
    >>> ls('../')
    'Error: unsafe path'
    >>> os.chdir(old)
    """
    if path is None or path == '':
        path = '.'
    if not is_path_safe(path):
        return 'Error: unsafe path'
    if os.path.isfile(path):
        return path
    if not os.path.isdir(path):
        return f"ls: cannot access '{path}': No such file or directory"
    names = [os.path.basename(p) for p in glob.glob(os.path.join(path, '*'))]
    return '  '.join(sorted(names))
