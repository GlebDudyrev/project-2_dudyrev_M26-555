import re


def _parse_value(raw_value):
    raw_value = raw_value.strip()

    if (
        len(raw_value) >= 2
        and raw_value[0] == raw_value[-1]
        and raw_value[0] in ('"', "'")
    ):
        return raw_value[1:-1]

    # Логические значения
    if raw_value.lower() == 'true':
        return True

    if raw_value.lower() == 'false':
        return False

    try:
        return int(raw_value)
    except ValueError:
        return None


def _parse_assignment(expression):
    parts = expression.split('=', maxsplit=1)

    if len(parts) != 2:
        print(f'Некорректное значение: {expression}. Попробуйте снова.')
        return None

    column, raw_value = map(str.strip, parts)

    if not column or not raw_value:
        print(f'Некорректное значение: {expression}. Попробуйте снова.')
        return None

    value = _parse_value(raw_value)

    if value is None:
        print(f'Некорректное значение: {raw_value}. Попробуйте снова.')
        return None

    return {column: value}


def parse_where(expression):
    return _parse_assignment(expression)


def parse_set(expression):
    return _parse_assignment(expression)


def parse_insert(command):
    match = re.fullmatch(
        r'insert\s+into\s+(\S+)\s+values\s*\((.*)\)\s*',
        command.strip(),
    )

    if match is None:
        print('Некорректная команда insert. Попробуйте снова.')
        return None

    table_name, raw_values = match.groups()

    values = []
    start = 0
    quote = None

    for index, char in enumerate(raw_values):
        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None

        elif char == ',' and quote is None:
            values.append(raw_values[start:index].strip())
            start = index + 1

    if quote is not None:
        print('Некорректное значение: незакрытые кавычки.')
        return None

    values.append(raw_values[start:].strip())

    parsed_values = []

    for raw_value in values:
        value = _parse_value(raw_value)

        if value is None:
            print(f'Некорректное значение: {raw_value}. Попробуйте снова.')
            return None

        parsed_values.append(value)

    return table_name, parsed_values


def parse_select(command):
    match = re.fullmatch(
        r'select\s+from\s+(\S+)(?:\s+where\s+(.+))?',
        command.strip(),
    )

    if match is None:
        print('Некорректная команда select. Попробуйте снова.')
        return None

    table_name, raw_where = match.groups()

    where_clause = None

    if raw_where is not None:
        where_clause = parse_where(raw_where)

        if where_clause is None:
            return None

    return table_name, where_clause


def parse_update(command):
    match = re.fullmatch(
        r'update\s+(\S+)\s+set\s+(.+?)\s+where\s+(.+)',
        command.strip(),
    )

    if match is None:
        print('Некорректная команда update. Попробуйте снова.')
        return None

    table_name, raw_set, raw_where = match.groups()

    set_clause = parse_set(raw_set)
    where_clause = parse_where(raw_where)

    if set_clause is None or where_clause is None:
        return None

    return table_name, set_clause, where_clause


def parse_delete(command):
    match = re.fullmatch(
        r'delete\s+from\s+(\S+)\s+where\s+(.+)',
        command.strip(),
    )

    if match is None:
        print('Некорректная команда delete. Попробуйте снова.')
        return None

    table_name, raw_where = match.groups()

    where_clause = parse_where(raw_where)

    if where_clause is None:
        return None

    return table_name, where_clause