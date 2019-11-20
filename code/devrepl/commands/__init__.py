import cmd, inspect
from . import *

class ReplCommand(cmd.Cmd):

    # called when the repl is started, after session and settings have been init'd
    def startup(self):
        pass

    def prompt_str(self):
        return ">> "

    def desc(self):
        return "base Repl"

