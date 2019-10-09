from pathlib import Path
from git import Repo
import datetime
from jira import JIRA
import webbrowser
import console_output as out

from . import ReplCommand


class Jira(ReplCommand):


    def do_jira(self, arg):
        if arg.startswith('b'):
            out.info('Opening browser.')
            webbrowser.open(self.session[
                'jira_url'] + '/issues/?jql=assignee%20%3D%20currentUser()%20and%20Resolution%20%3D%20Unresolved')
        else:
            open_issues = self.get_open_issues()
            for issue in open_issues:
                out.info(str(issue.fields.issuetype) + " " + str(
                    issue.fields.status) + " " + issue.key + "  " + issue.fields.summary)
                out.info("  -->  https://jira.pentaho.com/browse/" + issue.key)

    def get_open_issues(self):
        jira = JIRA({'server': self.settings['jira_url']},
                    basic_auth=(self.settings['jira_user'], self.settings['jira_pwd']))
        open_issues = jira.search_issues('assignee = currentUser() and Resolution = Unresolved')
        return open_issues

    def prompt_str(self):
        return None

