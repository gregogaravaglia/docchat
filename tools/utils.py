"""Shared helpers for the file tools, including the path safety check."""


def is_path_safe(path):
    """Return True if a path is relative and never climbs out of the folder.

    >>> is_path_safe('notes.txt')
    True
    >>> is_path_safe('tools/*.py')
    True
    >>> is_path_safe('/etc/passwd')
    False
    >>> is_path_safe('../secret.txt')
    False
    >>> is_path_safe('docs/../../secret.txt')
    False
    >>> is_path_safe('..')
    False
    >>> is_path_safe('C:\\\\Users\\\\grego')
    False
    """
    path = str(path)
    if path.startswith('/') or path.startswith('\\'):
        return False
    if len(path) > 1 and path[1] == ':':
        return False
    return '..' not in path
