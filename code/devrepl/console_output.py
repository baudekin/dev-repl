from colorama import Fore, Back, Style, init
from terminaltables import AsciiTable, DoubleTable, SingleTable

init(autoreset=True)


def print_command(command):
    print('{}{}{}'.format(Style.BRIGHT + Fore.GREEN, command, Style.RESET_ALL))


def info(message):
    print('{}{}{}'.format(Fore.BLUE, message, Style.RESET_ALL))


def warn(message):
    print('{}{}{}'.format(Style.BRIGHT + Fore.YELLOW, message, Style.RESET_ALL))


def error(message):
    print('{}*{}*{}'.format(Style.BRIGHT + Fore.RED, message, Style.RESET_ALL))


def highlighted(*messages):

    longest_message = max(messages, key=len)

    print(Fore.YELLOW + '_' * (len(longest_message) + 4))
    for m in messages[:-1]:
        m = m.ljust(len(longest_message))
        print('{}| {} |'.format(Fore.YELLOW, m))
    print('{}{}| {} |'.format('\033[1;4m', Fore.YELLOW, messages[-1].ljust(len(longest_message))))
    print()


def prompt_format(prompts):
    color = [Fore.LIGHTRED_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTWHITE_EX]
    promptstr = ''
    for i, prompt in enumerate(prompts[:-1]):
        promptstr += color[i % 3] + " " + prompt + " " * 3
        if len(promptstr) > 80:
            promptstr += '\n'
    return promptstr + '\n' + Fore.MAGENTA + prompts[-1]


def table(title, header=None, rows=[]):
    print(Style.RESET_ALL)

    if len(rows) > 0 and type(rows[0]) != tuple:
        rows = [(row,) for row in rows]
    if header and len(header) > 0:
        header = [Fore.YELLOW + item + Fore.RESET for item in header]
        tabdata = [header, rows]
    else:
        tabdata = rows

    table_instance = AsciiTable(tabdata, title)
    table_instance.outer_border = True
    table_instance.inner_heading_row_border = False
    table_instance.inner_column_border = False

    print(table_instance.table)
