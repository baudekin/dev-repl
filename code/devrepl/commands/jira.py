from jira import JIRA
import webbrowser
from .. import console_output as out

from . import ReplCommand


class Jira(ReplCommand):

    def do_jira(self, arg):
        """Lists cases assigned to the current user."""
        jql = self.settings['jira_jql']
        if arg.startswith('b'):
            out.info('Opening browser.')
            webbrowser.open(self.jira_url() + '/issues/?jql=' + jql)
        else:
            open_issues = self.get_open_issues()
            cases = [
                (issue.key, issue.fields.issuetype, issue.fields.summary, self.jira_url() + "/browse/" + issue.key)
                for
                issue in open_issues]
            out.table("Active Cases", rows=cases)

    def jira_url(self):
        return self.settings['jira_url']

    def do_jira_case_commit_message(self, arg):
        """Creates a git commit message template for cases currently assigned to you."""
        cases = [(issue.key, issue.fields.summary, self.jira_url() + "/browse/" + issue.key) for issue in self.get_open_issues()]
        msg = """
--------------------------------------------------------------------
[{}] {}
        
<msg>
        
{}
--------------------------------------------------------------------        
        """
        for case in cases:
            print(msg.format(case[0], case[1], case[2]))

    def get_open_issues(self):
        jql = self.settings['jira_jql']
        jira = JIRA({'server': self.settings['jira_url']},
                    basic_auth=(self.settings['jira_user'], self.settings['jira_pwd']))
        open_issues = jira.search_issues(jql)
        return open_issues

    def prompt_str(self):
        return None
