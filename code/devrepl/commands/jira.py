from pathlib import Path
from git import Repo
import datetime
from jira import JIRA
import webbrowser
import console_output as out

from . import ReplCommand


class Jira(ReplCommand):

    def do_init_jira(self, arg):
        url = input("Jira URL (default https://jira.pentaho.com): ")
        if len(url) > 4:
            self.session['jira_url'] = url
        else:
            self.session['jira_url'] = 'https://jira.pentaho.com'

        self.session['jira_user'] = input('Username:  ')
        self.session['jira_pwd'] = input('Password:  ')

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
        jira = JIRA({'server': self.session['jira_url']},
                    basic_auth=(self.session['jira_user'], self.session['jira_pwd']))
        open_issues = jira.search_issues('assignee = currentUser() and Resolution = Unresolved')
        return open_issues

    def prompt_str(self):
        return None

