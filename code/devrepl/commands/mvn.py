import subprocess
import console_output as out
from . import ReplCommand
from proc import cmd

class Mvn(ReplCommand):

    mvn_completions = (
        'clean', 'install', '-DrunITs', '-DskipTests', 'site', 'dependency:tree'
    )

    def do_b(self, arg):
        'Build current project.  Add the argument "st" to skip tests'
        build = ["mvn", "clean", "install", "-f", self.session['curproj'][1]]
        if arg == 'st':
            build = build + ["-DskipTests"]
        elif arg == 'q':  # build quick.  skip tests, use maven cache
            build = build + ["-DskipTests", "-o"]
        else:
            build = build + ["-DrunITs"]
        out.print_command(build)
        subprocess.call(build)

    def do_mvn(self, arg):
        params = arg.split(' ')
        build = ["mvn", "-f", self.session['curproj'][1]] + params
        out.print_command(build)
        subprocess.call(build)

    def complete_mvn(self, text, line, begidx, endidx):
        return [i.lstrip('-') for i in self.mvn_completions if i.startswith(text) or i.startswith('-' + text)]


    def prompt_str(self):
        return ''
