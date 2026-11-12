"""A pirate chatbot that can inspect the files in the current folder with tools."""

import argparse
import json
import os
import shlex
import sys

from dotenv import load_dotenv
from groq import Groq

from tools.calculate import calculate
from tools.cat import cat
from tools.grep import grep
from tools.ls import ls

MODEL = 'openai/gpt-oss-20b'
VISION_MODEL = 'meta-llama/llama-4-scout-17b-16e-instruct'
SYSTEM_PROMPT = (
    'You are a helpful assistant that answers questions about the files in '
    'the current folder. Use the ls, cat, and grep tools to look at files '
    'before answering, and the calculate tool for arithmetic. '
    'Answer in two to four plain sentences without tables or headings. '
    'You always speak like a pirate.'
)

# Tests may set this to a fake client; otherwise a Groq client is created per request.
client = None

FUNCTIONS = {
    'calculate': calculate,
    'ls': ls,
    'cat': cat,
    'grep': grep,
}

TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'calculate',
            'description': 'Evaluate an arithmetic expression such as "(2 + 3) * 4".',
            'parameters': {
                'type': 'object',
                'properties': {
                    'expression': {
                        'type': 'string',
                        'description': 'The arithmetic expression to evaluate.',
                    },
                },
                'required': ['expression'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'ls',
            'description': 'List the files in a folder. With no path, list the current folder.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'A relative folder path, such as "." or "tools".',
                    },
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'cat',
            'description': 'Return the full contents of a text file.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'A relative path to the file to read.',
                    },
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'grep',
            'description': 'Return every line matching a regex in the files matching a glob path.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'regex': {
                        'type': 'string',
                        'description': 'The regular expression to search for.',
                    },
                    'path': {
                        'type': 'string',
                        'description': 'A relative file path, which may contain globs such as "*.py".',
                    },
                },
                'required': ['regex', 'path'],
            },
        },
    },
]


def get_field(obj, name):
    """Read a field from either a dictionary or an object with attributes.

    >>> get_field({'content': 'hi'}, 'content')
    'hi'
    >>> from types import SimpleNamespace
    >>> get_field(SimpleNamespace(content='hi'), 'content')
    'hi'
    >>> get_field({}, 'tool_calls') is None
    True
    """
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def get_client():
    """Return the model client, creating a Groq client only when a request needs one.

    >>> from unittest.mock import patch
    >>> with patch('chat.Groq') as Groq, patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
    ...     made = get_client()
    >>> Groq.call_args.kwargs['api_key']
    'test-key'
    """
    if client is not None:
        return client
    load_dotenv()
    return Groq(api_key=os.environ.get('GROQ_API_KEY'))


def has_image(messages):
    """Return True if any message contains an image content block.

    >>> has_image([{'role': 'user', 'content': 'hi'}])
    False
    >>> has_image([{'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': 'data:'}}]}])
    True
    """
    return any(isinstance(m.get('content'), list) for m in messages)


def llm(messages, temperature=1, tools=None, retries=5):
    """Send messages (and optional tool descriptions) to the model and return its reply message.

    A request the service rejects because the model wrote malformed output is retried.

    >>> from unittest.mock import patch
    >>> from types import SimpleNamespace as NS
    >>> response = NS(choices=[NS(message=NS(content='Ahoy!', tool_calls=None))])
    >>> with patch('chat.Groq') as Groq:
    ...     Groq.return_value.chat.completions.create.return_value = response
    ...     print(llm([{'role': 'user', 'content': 'Hi'}], temperature=0).content)
    Ahoy!
    >>> kwargs = Groq.return_value.chat.completions.create.call_args.kwargs
    >>> kwargs['model'], kwargs['temperature'], 'tools' in kwargs
    ('openai/gpt-oss-20b', 0, False)
    >>> bad = RuntimeError("Error code: 400 - {'code': 'tool_use_failed'}")
    >>> with patch('chat.Groq') as Groq:
    ...     Groq.return_value.chat.completions.create.side_effect = [bad, response]
    ...     print(llm([{'role': 'user', 'content': 'Hi'}]).content)
    Ahoy!
    >>> with patch('chat.Groq') as Groq:
    ...     Groq.return_value.chat.completions.create.side_effect = RuntimeError('quota exhausted')
    ...     llm([{'role': 'user', 'content': 'Hi'}])
    Traceback (most recent call last):
    ...
    RuntimeError: quota exhausted
    """
    kwargs = {
        'messages': list(messages),
        'model': VISION_MODEL if has_image(messages) else MODEL,
        'temperature': temperature,
        'timeout': 60,
    }
    if tools:
        kwargs['tools'] = tools
    for attempt in range(retries + 1):
        try:
            completion = get_client().chat.completions.create(**kwargs)
            return completion.choices[0].message
        except Exception as error:
            flaky = 'tool_use_failed' in str(error) or 'output_parse_failed' in str(error)
            if not flaky or attempt == retries:
                raise


def run_tool(name, arguments):
    """Run the named tool with a dictionary of arguments and return its output as text.

    >>> run_tool('calculate', {'expression': '6 * 7'})
    '42'
    >>> run_tool('rm', {'path': 'notes.txt'})
    'Error: unknown tool rm'
    >>> run_tool('cat', {'file': 'notes.txt'})
    'Error: wrong arguments for cat'
    """
    if name not in FUNCTIONS:
        return f'Error: unknown tool {name}'
    try:
        return str(FUNCTIONS[name](**arguments))
    except TypeError:
        return f'Error: wrong arguments for {name}'


class Chat:
    """Store a conversation with the model and let it call file tools while answering.

    The model may request the calculate, ls, cat, and grep tools; each request is
    run in Python and its result is sent back before the model gives its answer.
    Users can also run the tools directly with slash commands such as /ls tools.

    An automatic tool call, using a fake client in place of the model:

    >>> from unittest.mock import patch
    >>> from types import SimpleNamespace as NS
    >>> def reply(content=None, calls=None):
    ...     return NS(choices=[NS(message=NS(content=content, tool_calls=calls))])
    >>> call = NS(id='call-1', type='function',
    ...           function=NS(name='calculate', arguments='{"expression": "6 * 7"}'))
    >>> with patch('chat.Groq') as Groq:
    ...     create = Groq.return_value.chat.completions.create
    ...     create.side_effect = [reply(calls=[call]), reply('It be 42.')]
    ...     chat = Chat(system='Be brief.')
    ...     print(chat.send_message('What is 6 * 7?'))
    It be 42.
    >>> second = create.call_args_list[1].kwargs['messages']
    >>> second[-2]['tool_calls'][0]['function']['name']
    'calculate'
    >>> second[-1]
    {'role': 'tool', 'tool_call_id': 'call-1', 'content': '42'}
    >>> [t['function']['name'] for t in create.call_args_list[0].kwargs['tools']]
    ['calculate', 'ls', 'cat', 'grep']
    >>> chat.messages[-1]
    {'role': 'assistant', 'content': 'It be 42.'}

    A manual slash command runs without the model, and its output reaches the next request:

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> os.chdir(tempfile.mkdtemp())
    >>> _ = open('notes.txt', 'w').write('Meet in Room 12.')
    >>> with patch('chat.Groq') as Groq:
    ...     chat = Chat(system='Be brief.')
    ...     print(chat.run_command('/cat notes.txt'))
    ...     Groq.called
    Meet in Room 12.
    False
    >>> with patch('chat.Groq') as Groq:
    ...     create = Groq.return_value.chat.completions.create
    ...     create.return_value = reply('Room 12, matey.')
    ...     print(chat.send_message('Where do we meet?'))
    Room 12, matey.
    >>> 'Meet in Room 12.' in create.call_args.kwargs['messages'][1]['content']
    True

    Debug mode prints every tool the model calls:

    >>> call = NS(id='call-2', type='function', function=NS(name='ls', arguments='{}'))
    >>> with patch('chat.Groq') as Groq:
    ...     create = Groq.return_value.chat.completions.create
    ...     create.side_effect = [reply(calls=[call]), reply('One file.')]
    ...     chat = Chat(system='Be brief.', debug=True)
    ...     print(chat.send_message('What files are here?'))
    [tool] ls {}
    One file.
    >>> os.chdir(old)
    """

    def __init__(self, system=SYSTEM_PROMPT, debug=False):
        """Start a conversation with a system prompt and register the four tools."""
        self.messages = [{'role': 'system', 'content': system}]
        self.tools = TOOLS
        self.functions = FUNCTIONS
        self.debug = debug

    def run_tool_call(self, call):
        """Run one tool call requested by the model and return the tool message to append.

        >>> from types import SimpleNamespace as NS
        >>> chat = Chat()
        >>> call = {'id': 'c1', 'type': 'function',
        ...         'function': {'name': 'calculate', 'arguments': '{"expression": "1 + 1"}'}}
        >>> chat.run_tool_call(call)
        {'role': 'tool', 'tool_call_id': 'c1', 'content': '2'}
        >>> bad = NS(id='c2', function=NS(name='ls', arguments='not json'))
        >>> chat.run_tool_call(bad)
        {'role': 'tool', 'tool_call_id': 'c2', 'content': 'Error: arguments were not valid JSON'}
        """
        function = get_field(call, 'function')
        name = get_field(function, 'name')
        try:
            arguments = json.loads(get_field(function, 'arguments') or '{}')
        except json.JSONDecodeError:
            result = 'Error: arguments were not valid JSON'
        else:
            if self.debug:
                print(f'[tool] {name} {json.dumps(arguments)}')
            result = run_tool(name, arguments)
        return {
            'role': 'tool',
            'tool_call_id': get_field(call, 'id'),
            'content': result,
        }

    def send_message(self, message, temperature=0.8, max_rounds=10):
        """Send a message, run any tools the model requests, and return its final reply.

        If the request fails, the history is restored and the error is raised.

        >>> from unittest.mock import patch
        >>> chat = Chat(system='Be brief.')
        >>> with patch('chat.Groq') as Groq:
        ...     Groq.return_value.chat.completions.create.side_effect = RuntimeError('quota exhausted')
        ...     chat.send_message('Hi')
        Traceback (most recent call last):
        ...
        RuntimeError: quota exhausted
        >>> chat.messages
        [{'role': 'system', 'content': 'Be brief.'}]
        """
        start = len(self.messages)
        self.messages.append({'role': 'user', 'content': message})
        try:
            for _ in range(max_rounds):
                reply = llm(self.messages, temperature=temperature, tools=self.tools)
                calls = list(get_field(reply, 'tool_calls') or [])
                if not calls:
                    content = get_field(reply, 'content') or ''
                    self.messages.append({'role': 'assistant', 'content': content})
                    return content
                request = {
                    'role': 'assistant',
                    'tool_calls': [
                        {
                            'id': get_field(call, 'id'),
                            'type': 'function',
                            'function': {
                                'name': get_field(get_field(call, 'function'), 'name'),
                                'arguments': get_field(get_field(call, 'function'), 'arguments'),
                            },
                        }
                        for call in calls
                    ],
                }
                if get_field(reply, 'content'):
                    request['content'] = get_field(reply, 'content')
                self.messages.append(request)
                for call in calls:
                    self.messages.append(self.run_tool_call(call))
        except BaseException:
            del self.messages[start:]
            raise
        content = 'Error: the model kept requesting tools without answering.'
        self.messages.append({'role': 'assistant', 'content': content})
        return content

    def run_command(self, line):
        """Run a slash command such as /ls tools directly, without contacting the model.

        The output of /calculate, /ls, /cat, and /grep is added to the conversation
        so the model can use it in later answers.

        >>> import os, tempfile
        >>> old = os.getcwd()
        >>> os.chdir(tempfile.mkdtemp())
        >>> _ = open('a.txt', 'w').write('TODO: write\\ndone\\n')
        >>> chat = Chat(system='Be brief.')
        >>> chat.run_command('/ls')
        'a.txt'
        >>> chat.run_command('/grep TODO a.txt')
        'TODO: write'
        >>> chat.run_command('/calculate (1 + 2) * 3')
        '9'
        >>> chat.messages[-1]['content']
        'I ran the command /calculate (1 + 2) * 3 and got this output:\\n9'
        >>> chat.run_command('/grep "TODO: w" a.txt')
        'TODO: write'
        >>> chat.run_command('/cat')
        'Usage: /cat path'
        >>> chat.run_command('/rm a.txt')
        'Unknown command /rm. Try /calculate, /ls, /cat, /grep, /compact, or /image.'
        >>> chat.run_command('/')
        'Unknown command /. Try /calculate, /ls, /cat, /grep, /compact, or /image.'
        >>> chat.run_command('/grep "(unclosed a.txt')
        'Error: invalid regex "(unclosed'
        >>> os.chdir(old)
        """
        command = line.strip()[1:]
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        name, args = (parts[0], parts[1:]) if parts else ('', [])
        usage = {
            'calculate': 'Usage: /calculate expression',
            'ls': 'Usage: /ls [path]',
            'cat': 'Usage: /cat path',
            'grep': 'Usage: /grep regex path',
            'image': 'Usage: /image path',
        }
        if name == 'calculate':
            output = calculate(command[len('calculate'):].strip())
        elif name == 'ls' and len(args) <= 1:
            output = ls(*args)
        elif name == 'cat' and len(args) == 1:
            output = cat(args[0])
        elif name == 'grep' and len(args) == 2:
            output = grep(args[0], args[1])
        elif name == 'compact':
            from tools.compact import compact
            return compact(self)
        elif name == 'image' and len(args) == 1:
            from tools.load_image import load_image
            return load_image(self, args[0])
        elif name in usage:
            return usage[name]
        else:
            return (f'Unknown command /{name}. '
                    'Try /calculate, /ls, /cat, /grep, /compact, or /image.')
        self.messages.append({
            'role': 'user',
            'content': f'I ran the command {line.strip()} and got this output:\n{output}',
        })
        return output


def parse_args(argv):
    """Parse the command-line options for the chat command.

    >>> parse_args([])
    Namespace(message=None, debug=False)
    >>> parse_args(['--debug', 'hello there'])
    Namespace(message='hello there', debug=True)
    """
    parser = argparse.ArgumentParser(
        prog='chat',
        description='Chat with a model that can read the files in this folder.',
    )
    parser.add_argument('message', nargs='?', help='send one message, print the reply, and exit')
    parser.add_argument('--debug', action='store_true', help='print each tool call the model makes')
    return parser.parse_args(argv)


def repl(temperature=0.8, argv=None):
    """Read messages and slash commands, print replies, and exit cleanly on end of input.

    >>> from unittest.mock import patch, MagicMock
    >>> from types import SimpleNamespace as NS
    >>> def reply(content):
    ...     return NS(choices=[NS(message=NS(content=content, tool_calls=None))])
    >>> inputs = MagicMock(side_effect=['Hello', '', '/calculate 2 + 2', 'Who are you?', EOFError])
    >>> with patch('builtins.input', inputs), patch('chat.Groq') as Groq, patch('builtins.print') as output:
    ...     Groq.return_value.chat.completions.create.side_effect = [reply('Ahoy!'), reply('A pirate!')]
    ...     repl(temperature=0, argv=[])
    >>> [call.args for call in output.call_args_list]
    [('Ahoy!',), ('4',), ('A pirate!',), ()]
    >>> inputs = MagicMock(side_effect=['/ls .', KeyboardInterrupt])
    >>> with patch('builtins.input', inputs), patch('chat.Groq') as Groq, patch('builtins.print'):
    ...     repl(argv=[])
    >>> Groq.called
    False
    >>> inputs = MagicMock(side_effect=['Hi', EOFError])
    >>> with patch('builtins.input', inputs), patch('chat.Groq') as Groq, patch('builtins.print') as output:
    ...     Groq.return_value.chat.completions.create.side_effect = RuntimeError('service unavailable')
    ...     repl(argv=[])
    >>> output.call_args_list[0].args
    ('Error: service unavailable',)
    >>> with patch('chat.Groq') as Groq, patch('builtins.print') as output:
    ...     Groq.return_value.chat.completions.create.return_value = reply('Arr!')
    ...     repl(argv=['Ahoy'])
    >>> output.call_args.args
    ('Arr!',)
    """
    if argv is None:
        program = os.path.basename(sys.argv[0])
        argv = sys.argv[1:] if program.startswith('chat') else []
    args = parse_args(argv)
    chat = Chat(debug=args.debug)
    if args.message:
        try:
            print(chat.send_message(args.message, temperature=temperature))
        except Exception as error:
            print(f'Error: {error}')
        return
    try:
        while True:
            line = input('chat> ')
            if not line.strip():
                continue
            if line.strip().startswith('/'):
                print(chat.run_command(line))
                continue
            try:
                print(chat.send_message(line, temperature=temperature))
            except Exception as error:
                print(f'Error: {error}')
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == '__main__':
    repl()
