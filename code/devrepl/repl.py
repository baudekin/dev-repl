import pickle

from commands.mvn import Mvn
from commands.projectinfo import ProjectInfo
from commands.git import Git
from commands.box import Box
from commands.jira import Jira
from commands.pentaho import Pentaho
from commands import ReplCommand
from pathlib import Path
import console_output as out
import json
from shutil import copyfile


def get_repl(command_list):
    class Repl(*command_list, ReplCommand):
        session = {}
        settings = {}
        dot_dir = str(Path.home()) + "/.devrepl/"

        def do_init_repl_dir(self):

            if not Path(self.dot_dir).exists():
                Path(self.dot_dir).mkdir()

        def emptyline(self):
            pass

        def preloop(self):
            self.init_prompt()

        def postcmd(self, stop, line):
            self.init_prompt()
            self.savestate()

        def prompt_str(self):
            return ""

        def do_exit(self, arg):
            exit(0)

        def init_prompt(self):
            prompts = []
            self.invoke_on_each_cmd("prompt_str", lambda s: prompts.append(s))
            self.prompt = out.prompt_format(list(filter(None, prompts)))

        def do_list_commands(self, args):
            for command in command_list:
                print(command().desc())

        def savestate(self):
            with open(self.dot_dir + '/session', 'wb') as fp:
                pickle.dump(self.session, fp)

        def loadstate(self):
            with open(self.dot_dir + "/settings.json") as settings:
                fixed_json = ''.join(line for line in settings if not line.lstrip().startswith('//'))
                self.settings = json.loads(fixed_json)

            if Path(self.dot_dir + "/session").exists():
                try:
                    with open(self.dot_dir + '/session', 'rb') as fp:
                        self.session = pickle.load(fp)
                except:
                    print('failed to load prev session')
            self.invoke_on_each_cmd("startup", lambda s:  None)

        def first_run(self):
            if not Path(self.dot_dir).exists():
                print("Starting devrepl for the first time.")
                print("Creating directory " + self.dot_dir)
                Path(self.dot_dir).mkdir()
                copyfile("settings.json", self.dot_dir + "settings.json")
                print("Edit the file " + self.dot_dir + "settings.json, and then restart.")
                return True
            else:
                return False

        def invoke_on_each_cmd(self, methodname, lamb):
            for clazz in type(self).__mro__:
                method = getattr(super(clazz, self), methodname, None)
                if method:
                    lamb(method())

    return Repl(completekey='tab')


import signal


def handler(signum, frame):
    pass


signal.signal(signal.SIGINT, handler)

repl = get_repl([Mvn, Git, ProjectInfo, Box, Pentaho, Jira])

if not repl.first_run():
    repl.loadstate()
    repl.cmdloop()



