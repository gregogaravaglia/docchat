"""A tool that reads a text file and returns its contents, like the shell's cat."""

from tools.utils import is_path_safe


def cat(path):
    r"""Return the contents of a text file, or an error message if it cannot be read.

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.mkdtemp()
    >>> os.chdir(tmp)
    >>> _ = open('notes.txt', 'w', encoding='utf-8').write('line one\nline two\n')
    >>> cat('notes.txt')
    'line one\nline two\n'
    >>> _ = open('wide.txt', 'w', encoding='utf-16').write('hola')
    >>> cat('wide.txt')
    'hola'
    >>> _ = open('image.bin', 'wb').write(b'\x89PNG\x00\xff\xfe\x80')
    >>> cat('image.bin')
    'Error: image.bin is not a text file'
    >>> _ = open('bad16.txt', 'wb').write(b'\xff\xfe\x00')
    >>> cat('bad16.txt')
    'Error: bad16.txt is not a text file'
    >>> cat('missing.txt')
    'Error: missing.txt does not exist'
    >>> os.mkdir('folder')
    >>> cat('folder')
    'Error: folder is a directory'
    >>> cat('/etc/passwd')
    'Error: unsafe path'
    >>> cat('../notes.txt')
    'Error: unsafe path'
    >>> os.chdir(old)
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return f'Error: {path} does not exist'
    except IsADirectoryError:
        return f'Error: {path} is a directory'
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            pass
    return f'Error: {path} is not a text file'
