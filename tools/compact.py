"""A tool that shrinks a conversation into a short summary to save context."""

PROMPT = (
    'Summarize the conversation so far in at most five short lines. '
    'Keep any facts, file names, and results that later questions may need.'
)


def compact(chat):
    """Replace a chat's history with a model-written summary of at most five lines.

    >>> from unittest.mock import patch
    >>> from types import SimpleNamespace as NS
    >>> from chat import Chat
    >>> chat = Chat(system='Be brief.')
    >>> chat.messages.append({'role': 'user', 'content': 'My name is Grego.'})
    >>> summary = 'The user is Grego.'
    >>> with patch('chat.Groq') as Groq:
    ...     create = Groq.return_value.chat.completions.create
    ...     create.return_value = NS(choices=[NS(message=NS(content=summary, tool_calls=None))])
    ...     print(compact(chat))
    The user is Grego.
    >>> create.call_args.kwargs['messages'][1]
    {'role': 'user', 'content': 'My name is Grego.'}
    >>> chat.messages
    [{'role': 'system', 'content': 'The user is Grego.'}]
    >>> long_summary = '\\n'.join(f'line {i}' for i in range(1, 8))
    >>> with patch('chat.Groq') as Groq:
    ...     create = Groq.return_value.chat.completions.create
    ...     create.return_value = NS(choices=[NS(message=NS(content=long_summary, tool_calls=None))])
    ...     print(compact(chat))
    line 1
    line 2
    line 3
    line 4
    line 5
    >>> len(chat.messages)
    1
    """
    import chat as chat_module
    request = list(chat.messages) + [{'role': 'user', 'content': PROMPT}]
    reply = chat_module.llm(request, temperature=0)
    summary = (chat_module.get_field(reply, 'content') or '').strip()
    lines = summary.splitlines()
    if len(lines) > 5:
        summary = '\n'.join(lines[:5])
    chat.messages = [{'role': 'system', 'content': summary}]
    return summary
