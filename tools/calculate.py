"""A calculator tool that safely evaluates arithmetic expressions."""

import re

ALLOWED = re.compile(r'^[0-9\s.+\-*/%()]+$')


def calculate(expression):
    """Evaluate an arithmetic expression and return the result as a string.

    >>> calculate('2 + 3')
    '5'
    >>> calculate('(4 + 6) * 3 - 1')
    '29'
    >>> calculate('7 / 2')
    '3.5'
    >>> calculate('2 ** 10 % 1000')
    '24'
    >>> calculate('1 / 0')
    'Error: division by zero'
    >>> calculate('2 +')
    'Error: invalid expression'
    >>> calculate('')
    'Error: invalid expression'
    >>> calculate("__import__('os').remove('notes.txt')")
    'Error: only numbers, spaces, parentheses, and + - * / % ** // are allowed'
    >>> calculate('abs(-3)')
    'Error: only numbers, spaces, parentheses, and + - * / % ** // are allowed'
    """
    if not ALLOWED.match(expression):
        if expression.strip() == '':
            return 'Error: invalid expression'
        return ('Error: only numbers, spaces, parentheses, '
                'and + - * / % ** // are allowed')
    try:
        result = eval(expression, {'__builtins__': {}}, {})
    except ZeroDivisionError:
        return 'Error: division by zero'
    except (SyntaxError, TypeError, ValueError):
        return 'Error: invalid expression'
    return str(result)
