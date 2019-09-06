from pathlib import Path
from colorama import Fore, Back, Style, init
import console_output as out
from proc import cmd
import requests
import subprocess

# def jstat():
#     result = subprocess.run(['jstat', '-gc', '94079'], stdout=subprocess.PIPE)
#     return ','.join(str(result.stdout).split("\\n")[1].split())
#
# jstat()

def rm(path):
    if Path(path).exists() and Path(path).is_absolute():
        cmd(["rm", path], ".")



def rm_recursive(path):
    if Path(path).exists() and Path(path).is_absolute():
        cmd(["rm", '-rf',  path], '.')


def replace_in_file(filename, search, replace):
    with open(filename, 'r') as file :
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
    twopercent = float(resp.headers['content-length']) * .02
    cur = 0
    print(url + '=>' + destination)
    print('[<-' + Back.LIGHTBLUE_EX + Fore.BLACK + Style.BRIGHT + '#', end='', flush=True)
    with open(destination, 'wb') as fd:
        for chunk in resp.iter_content(chunk_size=128):
            cur += 128
            if (cur > twopercent):
                cur = 0
                print('#', end='', flush=True)
            fd.write(chunk)

    print(Fore.RESET + Back.RESET + Style.RESET_ALL + '->]\nCOMPLETED')
