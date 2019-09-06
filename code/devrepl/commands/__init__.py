import cmd, inspect

import commands

class ReplCommand(cmd.Cmd):
    def config_items(self):
        return "";

    def prompt_str(self):
        return ">> "

    def desc(self):
        return "base Repl"

    def get_session(self):
        return {}

    def sync_session(self):
        pass

def get_commands():
    classes = []
    for child_module in inspect.getmembers(commands, inspect.ismodule):
        classes += [clazz[1] for clazz in inspect.getmembers(child_module[1], inspect.isclass) if issubclass(clazz[1], ReplCommand) and not(clazz[1] == ReplCommand)]
    return classes
