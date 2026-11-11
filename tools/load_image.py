"""A tool that adds a local image to the conversation so a vision model can see it."""

import base64
import mimetypes

from tools.utils import is_path_safe


def load_image(chat, path):
    """Append a relative local image to a chat's history as a base64 data URL.

    >>> import os, tempfile
    >>> from chat import Chat
    >>> old = os.getcwd()
    >>> os.chdir(tempfile.mkdtemp())
    >>> _ = open('dot.png', 'wb').write(b'\\x89PNG fake bytes')
    >>> chat = Chat(system='Be brief.')
    >>> load_image(chat, 'dot.png')
    'Loaded image dot.png'
    >>> chat.messages[-1]
    {'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,iVBORyBmYWtlIGJ5dGVz'}}]}
    >>> load_image(chat, '/etc/photo.png')
    'Error: unsafe path'
    >>> load_image(chat, '../photo.png')
    'Error: unsafe path'
    >>> load_image(chat, 'missing.png')
    'Error: missing.png does not exist'
    >>> len(chat.messages)
    2
    >>> os.chdir(old)
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except (FileNotFoundError, IsADirectoryError):
        return f'Error: {path} does not exist'
    mime = mimetypes.guess_type(path)[0] or 'image/png'
    url = f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')
    chat.messages.append({
        'role': 'user',
        'content': [{'type': 'image_url', 'image_url': {'url': url}}],
    })
    return f'Loaded image {path}'
