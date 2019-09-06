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


def get_repl(command_list):
    class Repl(*command_list, ReplCommand):
        session = {}
        session['dot_dir'] = str(Path.home()) + "/.dev2/"

        def do_init_repl_dir(self):
            d = input('What directory should be used for dev repl downloads / session data (default {})'.format(
                self.session['dot_dir']))
            if len(d) > 0:
                self.session['dot_dir'] = d
            if not Path(self.session['dot_dir']).exists():
                Path(self.session['dot_dir']).mkdir()

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

        def dot_dir(self):
            return self.session['dot_dir']

        def savestate(self):
            with open(self.dot_dir() + '/session', 'wb') as fp:
                pickle.dump(self.session, fp)

        def loadstate(self):
            if Path(self.dot_dir() + "/session").exists():
                try:
                    with open(self.dot_dir() + '/session', 'rb') as fp:
                        self.session = pickle.load(fp)
                except:
                    print('failed to load prev session')

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
repl.loadstate()
repl.cmdloop()
