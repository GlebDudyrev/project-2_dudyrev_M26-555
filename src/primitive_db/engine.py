import prompt

PROMPTS_TEMPLATES = {
    'help': (
        '\n<command> exit - выйти из программы\n'
        '<command> help - справочная информация\n'
        'Введите команду: '
    ),
}


def welcome():
    print('Первая попытка запустить проект!')

    print('\n***')

    command = prompt.string(PROMPTS_TEMPLATES['help'])

    while command != 'exit':
        try:
            command = prompt.string(PROMPTS_TEMPLATES[command])
        except KeyError:
            raise AssertionError(f'Unknown command: {command}')
