from pathlib import Path
from colorama import Fore, Back, Style
import devrepl.console_output as out
from devrepl.proc import cmd
import requests
from dateutil.parser import *


def rm(path):
    if Path(path).exists() and Path(path).is_absolute():
        cmd(["rm", path], ".")


def rm_recursive(path):
    if Path(path).exists() and Path(path).is_absolute():
        cmd(["rm", '-rf', path], '.')


def replace_in_file(filename, search, replace):
    with open(filename, 'r') as file:
        content = file.read()
        content = content.replace(search, replace)
    if content:
        with open(filename, 'w') as file:
            file.write(content)


def httpget(url, destination):
    resp = requests.get(url, stream=True)
    if not resp.headers['content-length']:
        out.error("Couldn't load " + url)
        return
    last_modified = None
    if resp.headers['Last-modified']:
        last_modified = resp.headers['Last-modified']
    two_percent = float(resp.headers['content-length']) * .02
    cur = 0
    print(url + '=>' + destination)
    print('[<-' + Back.LIGHTBLUE_EX + Fore.BLACK + Style.BRIGHT + '#', end='', flush=True)
    with open(destination, 'wb') as fd:
        for chunk in resp.iter_content(chunk_size=128):
            cur += 128
            if cur > two_percent:
                cur = 0
                print('#', end='', flush=True)
            fd.write(chunk)

    print(Fore.RESET + Back.RESET + Style.RESET_ALL + '->]\nCOMPLETED')
    return parse(last_modified)
