from pathlib import Path
from git import Repo
import datetime
from jira import JIRA
import webbrowser
import console_output as out

from . import ReplCommand


class Jira(ReplCommand):


    def do_jira(self, arg):
        jira_url = self.settings['jira_url']
        jql = self.settings['jira_jql']
        if arg.startswith('b'):
            out.info('Opening browser.')
            webbrowser.open(jira_url + '/issues/?jql=' + jql)
        else:
            open_issues = self.get_open_issues()
            cases = [(issue.key, issue.fields.issuetype, issue.fields.summary, jira_url + "/browse/" + issue.key) for issue in open_issues]
            out.table("Active Cases", rows=cases)

    def get_open_issues(self):
        jql = self.settings['jira_jql']
        jira = JIRA({'server': self.settings['jira_url']},
                    basic_auth=(self.settings['jira_user'], self.settings['jira_pwd']))
        open_issues = jira.search_issues(jql)
        return open_issues

    def prompt_str(self):
        return None

