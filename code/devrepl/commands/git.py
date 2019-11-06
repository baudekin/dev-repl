import subprocess
from pathlib import Path
from proc import cmd
import os
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
        tree_actions(self.settings['proj_dir'],
                     (lambda direntry: direntry.path.endswith('/.git'),
                      lambda direntry: self.pull_master(direntry.path)), maxdepth=5)

    def do_fetch_all(self, arg):
        'Walks the project dir, issuing a fetch on master.'
        tree_actions(self.settings['proj_dir'],
                     (lambda direntry: direntry.path.endswith('/.git'),
                      lambda direntry: self.fetch_master(direntry.path)), maxdepth=5)

    def do_gitlogs(self, arg):
        if arg:
            days = arg
        else:
            days = '4'
        logs = []
        tree_actions(self.settings['proj_dir'],
                     (lambda direntry: direntry.path.endswith('/.git'),
                      lambda direntry: self.logs(direntry.path, logs, days)), maxdepth=5)
        out.table('Changes in the past {} days'.format(days), rows=logs)

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

    def logs(self, path, log_accum, days):
        branches = cmd(['git', 'branch', '-a'], path, display=False)

        if 'upstream/master' not in str(branches):
            # only look for changes on upstream/master branch
            return
       # cmd(['git', 'fetch', 'upstream', 'master'], path, display=False)
        url = cmd(['git', 'remote', 'get-url', 'upstream'], path, display=False, stderr=None)

        if len(url) > 0:
            url = url[0].decode('utf-8')
            url = url.replace('.git', '').replace('\n', '').replace('git://', 'https://')

        path = path[:-4]
        logcmd = ['git', 'log', '--since="{} days ago"'.format(days),
                  '--format=%an!$' + url + '/commit/%h!$%ad!$%s',
                  '--no-merges',
                  '--date=relative',
                  'upstream/master']
        logs = cmd(logcmd, path, display=True, stderr=None)
        if len(logs) > 0 and len(logs[0]) > 5:
            logs = logs[0].decode("utf-8").split('\n')
        else:
            return []
        logs = [tuple([os.path.basename(path[:-1])] + row.split('!$')) for row in logs if len(row) > 5]
        # print(str(logs))
        log_accum += logs

    def fetch_master(self, path):
        path = path[:-4]
        if self.upstream_exists(path):
            fum = ['git', 'fetch', 'upstream', 'master']
            out.print_command(fum)
            cmd(fum, path)
        else:
            print('{} Has no upstream.  Not fetching'.format(path))

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
