from re import S
import sys
import unittest
import os
import gitlab.v4.objects.projects
import gitlab.v4.objects
from random import randint
from gitlabbot import YamlValidator, GitlabIssue, GitlabAPIHandler


class YamlTest(unittest.TestCase):

    def testCorrectYaml(self):
        with open("UnitTests/YamlSamples/CorrectYaml.yml", "r", encoding="utf-8") as yaml_str:
            yaml_valid = YamlValidator(yaml_str.read())
            results = yaml_valid.validate_yaml()
            self.assertTrue(results.success)

    def testMissingRequired(self):
        with os.scandir("UnitTests/YamlSamples") as yaml_files:
            for entry in yaml_files:
                if(entry.name.find("Missing") != -1):
                    with open("UnitTests/YamlSamples/"+entry.name, "r", encoding="utf-8") as yaml_file:
                        print("Testing "+entry.name)
                        yaml_valid = YamlValidator(yaml_file.read())
                        results = yaml_valid.validate_yaml()
                        self.assertFalse(results.success)


class GitlabIssueTest(unittest.TestCase):
    TOKEN: str
    URL: str
    PROJECTID: str
    __issue: gitlab.v4.objects.ProjectIssue
    __gitlab_issue: GitlabIssue
    __project: gitlab.v4.objects.Project

    def createNewIssue(self):
        testBot = GitlabAPIHandler(self.TOKEN, self.PROJECTID, self.URL)
        self.__project = testBot.get_project()
        issue_data = self.__project.issues.create({'title': '{}'.format(randint(0, 100)),
                                                   'description': 'Something.'})
        issue_id = issue_data.attributes["iid"]
        self.__issue = self.__project.issues.get(issue_id)
        self.__gitlab_issue = GitlabIssue(self.__project, issue_id)

    def testUpdateLabels(self):
        self.createNewIssue()
        label = ["test"]
        self.__gitlab_issue.update_tags(label)
        # Update the issue variable
        self.__issue = self.__project.issues.get(self.__gitlab_issue.get_iid())
        expr = self.__issue.attributes["labels"] == label
        self.deleteNewIssue()
        self.assertTrue(expr)

    def testPrintComment(self):
        self.createNewIssue()
        self.__gitlab_issue.print_comment("Hello world, this is a test.")
        self.__issue = self.__project.issues.get(self.__gitlab_issue.get_iid())
        expr = self.__issue.notes.list() is not []
        self.deleteNewIssue()
        self.assertTrue(expr)

    def testUpdateLabelAndPrintComment(self):
        self.createNewIssue()
        # This is the label
        label = ["test"]
        self.__gitlab_issue.update_tags(label)
        # This is the comment
        self.__gitlab_issue.print_comment("Hello world, this is a test.")
        # Update the issue variable
        self.__issue = self.__project.issues.get(self.__gitlab_issue.get_iid())

        expr = (self.__issue.attributes["labels"] == label) and (self.__issue.notes.list() is not [])
        self.deleteNewIssue()
        self.assertTrue(expr)

    def deleteNewIssue(self):
        self.__project.issues.delete(self.__gitlab_issue.get_iid())
        self.__issue = None
        self.__gitlab_issue = None


if __name__ == '__main__':
    if len(sys.argv) > 1:
        GitlabIssueTest.URL = sys.argv.pop()
        GitlabIssueTest.PROJECTID = sys.argv.pop()
        GitlabIssueTest.TOKEN = sys.argv.pop()
    unittest.main()
