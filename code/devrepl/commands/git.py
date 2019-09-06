from pathlib import Path
from proc import cmd

import console_output as out

from treewalk import tree_actions

from . import ReplCommand


class Git(ReplCommand):
    git_path = ""
    repo = None

    def do_softreset(self, arg):
        output = cmd(["git", "log", "--oneline", "-2"], Path(self.session['curproj'][1]).parent.as_posix())
        id = str(output).split("\\n")[1][0:8]
        cmd(["git", "reset", "--soft", id])

    def master(self, pop=True):
        print("stash current changes (if any)")
        self.repo.git.stash()
        print("checkout master")
        self.repo.git.checkout("master")
        print("fetch upstream, merge")
        self.repo.git.fetch("upstream")
        self.repo.git.merge("upstream/master")

        if pop and len(self.repo.git.stash("list")) > 0:
            print("stash pop")
            self.repo.git.stash("pop")

    def do_git(self, arg):
        proj_dir = Path(self.session['curproj'][1]).parent.as_posix()
        cmd(['git'] + arg.split(' '), proj_dir, stdout=None, display=False)

    def do_pull_all_clean(self, arg):
        'Walks the project dir, issuing a pull on master if no local changes detected.'
        tree_actions(self.session['proj_dir'],
                     (lambda direntry: direntry.path.endswith('/.git'),
                      lambda direntry: self.pull_master(direntry.path)), maxdepth=5)

    def git_dir_is_clean(self, dir):
        res = cmd(['git', "--work-tree=" + dir, "--git-dir=" + dir + "/.git", "status", "--porcelain"], dir)
        return len(str(res).split('\\n')) == 1

    def desc(self):
        return "foo desc"

    def prompt_str(self):
        if self.session.get('curproj'):
            stdout, stderr = cmd(["git", "status", "-b", "--porcelain"],
                                 wd=Path(self.session['curproj'][1]).parent.as_posix(), display=False)
            return '[{}]'.format(str(stdout).split("\\n", 1)[0][2:])

    def upstream_exists(self, path):
        upstream_check = ['git', 'config', 'remote.upstream.url']
        return len(str(cmd(upstream_check, path))) > 4

    def pull_master(self, path):
        path = path[:-4]
        if self.git_dir_is_clean(path) and self.upstream_exists(path):
            pcm = ['git', 'checkout', 'master']
            out.print_command(pcm)
            cmd(pcm, path)
            pum = ['git', 'pull', 'upstream', 'master']
            out.print_command(pum)
            cmd(pum, path)
        else:
            print('{} is not in a clean state.  Not updating'.format(path))
