import subprocess
from pathlib import Path
from ..proc import cmd
import os
from .. import console_output as out

from ..treewalk import tree_actions

from . import ReplCommand


class Git(ReplCommand):
    git_path = ""
    repo = None

    def do_softreset(self, arg):
        """Executes `git reset --soft <hash>` where <hash> is the previous commit id"""
        proj_path = Path(self.session['curproj'][1]).parent.as_posix()
        output = cmd(["git", "log", "--oneline", "-2", "--format=%H"], proj_path)
        id = str(output).split("\\n")[1][0:14]
        cmd(["git", "reset", "--soft", id], proj_path)

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
        """executes git within the current project."""
        proj_dir = Path(self.session['curproj'][1]).parent.as_posix()
        cmd(['git'] + arg.split(' '), proj_dir, stdout=None, display=False)

    def do_pull_all_clean(self, arg):
        """Walks the project dir, issuing a pull on master if no local changes detected."""
        tree_actions(self.settings['proj_dir'],
                     lambda direntry: direntry.path.endswith('/.git'),
                     lambda direntry: self.pull_master(direntry.path), maxdepth=5)

    def do_fetch_all(self, arg):
        """Walks the project dir, issuing a fetch on master."""
        tree_actions(self.settings['proj_dir'],
                     lambda direntry: direntry.path.endswith('/.git'),
                     lambda direntry: self.fetch_master(direntry.path), maxdepth=5)

    def do_logs_for_file(self, arg):
        """Queries *all* logs stored in devrepl.db for changed files LIKE %arg%"""
        conn = self.connect_devrepl_db()
        c = conn.cursor()

        query = """
select substr(commit_date,2,10), author, jira_case, substr(summary,1,40), github_url, changed_file 
from logs
where changed_file like '%{}%'
order by commit_date desc
limit 40

        """.format(arg)
        out.info(query)
        results = c.execute(query)
        out.table("Logs with filename like " + arg, rows=[row for row in results])

    def do_gitlogs(self, arg):
        if arg:
            days = arg
        else:
            days = '4'
        logs = []
        tree_actions(self.settings['proj_dir'],
                     lambda direntry: direntry.path.endswith('/.git'),
                     lambda direntry: self.logs(direntry.path, logs, days), maxdepth=5)
        out.table('Changes in the past {} days'.format(days), rows=logs)

    def git_dir_is_clean(self, dir):
        res = cmd(['git', "--work-tree=" + dir, "--git-dir=" + dir + "/.git", "status", "--porcelain"], dir)
        return len(str(res).split('\\n')) == 1

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
        url = cmd(['git', 'remote', 'get-url', 'upstream'], path, display=False)

        if len(url) > 0:
            url = url[0].decode('utf-8')
            url = url.replace('.git', '').replace('\n', '').replace('git://', 'https://')

        path = path[:-4]
        logcmd = ['git', 'log', '--since="{} days ago"'.format(days),
                  '--format=%an!$' + url + '/commit/%h!$%ad!$%s',
                  '--no-merges',
                  '--date=relative',
                  'upstream/master']
        logs = cmd(logcmd, path, display=False)
        if len(logs) > 0 and len(logs[0]) > 5:
            logs = logs[0].decode("utf-8").split('\n')
        else:
            return []
        logs = [tuple(row.split('!$')) for row in logs if len(row) > 5]
        logs = [(r[:2] + (r[3][0:70],)) for r in logs]  # trim the commit description
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

    @staticmethod
    def git_upstream_url(path):
        url = cmd(['git', 'remote', 'get-url', 'upstream'], path, display=False)
        if len(url) > 0:
            url = url[0].decode('utf-8')
            url = url.replace('.git', '').replace('\n', '').replace('git://', 'https://')
        return url

    def do_load_logs(self, arg):
        tree_actions(self.settings['proj_dir'],
                     lambda direntry: direntry.path.endswith('/.git'),
                     lambda direntry: self.load_logs(direntry.path), maxdepth=5)

    def load_logs(self, path):
        path = path[:-4]
        out.info("Loading logs for " + path)
        project_name = Path(path).name
        logs = Git.flattened_logs(path)
        if not logs:
            out.info("No logs found for " + path)
            return

        conn = self.connect_devrepl_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs
        (commit_date timestamp, author text, github_url text, summary text, body text, jira_case text, changed_file text, git_project text)
        ''')
        c.execute("delete from logs where git_project = '{}'".format(project_name))
        for entry in logs:
            try:
                insert = '''INSERT INTO logs (commit_date, author, github_url, summary, body, jira_case, changed_file, git_project) VALUES
                ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')
                '''.format(*entry, project_name)
                c.execute(insert)
            except:
                print(insert)
        conn.commit()
        conn.close()

    @staticmethod
    def flattened_logs(path):
        branches = cmd(['git', 'branch', '-a'], path, display=False)

        if 'upstream/master' not in str(branches):
            # only look for changes on upstream/master branch
            return

        url = Git.git_upstream_url(path)

        logcmd = ['git', 'log',
                  '--format=!+$+%cI!$%an!$' + url + '/commit/%h!$%s!$%b!-$',
                  '--no-merges',
                  # '--date=relative',
                  '--name-only',
                  'upstream/master']
        logs = cmd(logcmd, path, display=True)

        if len(logs) > 0 and len(logs[0]) > 5:
            logs = logs[0].decode(encoding='utf-8', errors='ignore').replace("'", "''").split('!+$')[1:]
            logs = [[part[0], part[1]] for part in [commit.split('!-$') for commit in logs]]
        parsed_logs = []

        for commit_lines in logs:
            # log lines will start with +
            cur_log_entry = Git.prepare_log_entry(commit_lines[0].split('!$'))
            for file in commit_lines[1].split('\n'):
                if len(file.strip()) > 0:
                    entry = cur_log_entry.copy()
                    entry.append(file)
                    parsed_logs.append(entry)

        return parsed_logs

    @staticmethod
    def prepare_log_entry(log_entry):
        """
        """
        log_entry[4] = log_entry[4].replace("$n!", "\n")
        summary = log_entry[3]
        jira_case = ''
        if summary.startswith('[') and summary.find(']') > 1:
            jira_case = summary[:summary.find(']') + 1]
        log_entry.append(jira_case)
        return log_entry
