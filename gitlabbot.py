import gitlab
import gitlab.v4.objects.projects
import gitlab.v4.objects
import os
import sys
from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError


class Response:
    success: bool
    message: str

    def __init__(self, success, message):
        self.success = success
        self.message = message


class IssueComment(Response):
    labels: str

    def __init__(self, success: bool, message: str, labels: str):
        super().__init__(success, message)
        self.labels = labels


class YamlValidatorReturn(IssueComment):
    yaml_obj: object

    def __init__(self, success: bool, message: str, labels: str, yaml_obj):
        super().__init__(success, message, labels)
        self.yaml_obj = yaml_obj


class GitlabBot:
    """This creates a client to access the Gitlab API

    Returns:
        gitlab.Gitlab: A gitlab client used for access to the API
    """
    _token: str
    _url: str
    _client: gitlab.Gitlab

    def __init__(self, token: str, url: str):
        self.gitlab_handler = None
        self._token = token
        self._url = url
        self.start()

    def start(self) -> None:
        self._client = gitlab.Gitlab(private_token=self._token, url=self._url)

    def get_client(self) -> gitlab.Gitlab:
        return self._client


class GitlabAPIHandler(GitlabBot):
    _project_id: str
    _project: gitlab.v4.objects.projects.Project

    def __init__(self, token: str, project_id: str, url: str):
        super().__init__(token, url)
        self._project_id = project_id
        self.retrieve_project()

    def get_project_id(self) -> str:
        return self._project_id

    def get_project(self) -> gitlab.v4.objects.projects.Project:
        return self._project

    def retrieve_project(self) -> None:
        self._project = self._client.projects.get(id=int(self._project_id))

    def create_issue_handler(self, labels: list[str], state='opened',
                             order_by='created_at', sort='desc'):
        return GitlabIssuesHandler(self, labels, state, order_by, sort)


class GitlabIssue:
    __iid: str
    __issue: gitlab.v4.objects.ProjectIssue

    def __init__(self, project: gitlab.v4.objects.projects.Project, issue_iid: str):
        self.__iid = issue_iid
        self.__issue = project.issues.get(issue_iid)

    def get_iid(self) -> str:
        return self.__iid

    def get_id(self) -> str:
        return self.__issue.attributes['id']

    def get_description(self) -> str:
        return self.__issue.attributes['description']

    def update_tags(self, new_labels: list[str]):
        self.__issue.labels = new_labels
        self.__issue.save()

    def print_comment(self, message: str):
        self.__issue.notes.create({'body': message})
        self.__issue.save()
        print("The issue has been updated")


class GitlabIssuesHandler:
    __issues: list[GitlabIssue]
    __project: gitlab.v4.objects.projects.Project
    __labels: list[str]
    __state: str = ""
    __order_by: str = ""
    __sort: str = ""

    def __init__(self, project: GitlabAPIHandler, labels: list[str], 
                 state='opened', order_by='created_at', sort='desc'):
        self.__project = project.get_project()
        self.__labels = labels
        self.__state = state
        self.__order_by = order_by
        self.__sort = sort
        self.__issues = []
        self.__retrive_issues()

    def __retrive_issues(self):
        # Create a temporary list for storing iids to prevent duplicates
        list_of_iid = []
        for label in self.__labels:
            results = self.__project.issues.list(labels=label,
                                                 state=self.__state,
                                                 order_by=self.__order_by,
                                                 sort=self.__sort)
            for result in results:
                result_iid = result.attributes['iid']
                if result_iid not in list_of_iid:
                    list_of_iid.append(result_iid)
                    new_issue = GitlabIssue(self.__project, result_iid)
                    self.__issues.append(new_issue)

    def validate_issues(self):
        for issue in self.__issues:
            validate_yaml = YamlValidator(issue.get_description())
            result = validate_yaml.validate_yaml()
            issue.update_tags(result.labels)
            issue.print_comment(result.message)
            if result.success:
                project_id = sys.argv[2]
                mr = GitlabMergeRequest(result.yaml_obj, issue.get_id(), self.__project)
                mr.create_merge_request()

    def get_issues(self):
        return self.__issues


class GitlabMergeRequest:
    __target_branch: str = 'main'
    __yaml_obj: object
    __project: gitlab.v4.objects.projects.Project
    __id: str
    __target_project_id: str

    def __init__(self, yaml_obj: object, issue_id: str, project: gitlab.v4.objects.projects.Project):
        self.__yaml_obj = yaml_obj
        self.__project = project
        self.__id = issue_id
        self.__source_branch = 'Profile-Request-{}'.format(issue_id)
        self.__target_project_id = project.get_id()

    def create_merge_request(self) -> None:
        branch = GitlabBranches(self.__project, "main", self.__id)
        branch.create_new_branch()
        try:
            commit = GitlabCommits(self.__yaml_obj, self.__project, self.__id)
            commit.create_commit()
            self.__project.mergerequests.create({'source_branch': self.__source_branch,
                                                 'target_branch': self.__target_branch,
                                                 'target_project_id': int(self.__target_project_id),
                                                 'source_project_id': int(self.__target_project_id),
                                                 'title': 'Profile request #{}'.format(self.__id)})
        except gitlab.GitlabCreateError as error:
            print("Error creating merge request: {}".format(error))


class GitlabBranches:
    __project: gitlab.v4.objects.projects.Project
    __ref_branch: str
    __id: str

    def __init__(self, project: gitlab.v4.objects.projects.Project, ref_branch: str, issue_id: str):
        self.__project = project
        self.__ref_branch = ref_branch
        self.__id = issue_id

    def create_new_branch(self) -> None:
        if self.branch_not_exists():
            try:
                print('Profile-Request-{}'.format(self.__id))
                self.__project.branches.create({'branch': 'Profile-Request-{}'.format(self.__id),
                                                'ref': self.__ref_branch})
            except gitlab.GitlabCreateError as error:
                print("Error creating branch: {}".format(error))
        else:
            print("Error creating branch: Branch already exists")

    def branch_not_exists(self) -> bool:
        branches = self.__project.branches.list(search='Profile-Request-{}'.format(self.__id))
        if branches is []:
            return False
        else: 
            return True


class GitlabCommits:
    __yaml_obj: object
    __project: gitlab.v4.objects.projects.Project

    def __init__(self, yaml_obj: object, project: gitlab.v4.objects.projects.Project, 
                 issue_id: str):
        self.__yaml_obj = yaml_obj
        self.__project = project
        self.__issue_id = issue_id

    def create_commit(self) -> None:
        with open("{}.yml".format(self.__yaml_obj['id']), 'w+') as file:
            yaml.dump(self.__yaml_obj, file)

            data = {
                'branch': 'Profile-Request-{}'.format(self.__issue_id),
                'commit_message': 'Commit for profile request {}'.format(self.__yaml_obj["id"]),
                'actions': [
                    {
                        'action': 'create',
                        'file_path': '{}.yml'.format(self.__yaml_obj['id']),
                        'content': open('{}.yml'.format(self.__yaml_obj['id'])).read(),
                    }
                ]
            }

            self.commit(data)

    def commit(self, data) -> None:
        try:
            self.__project.commits.create(data)
        except Exception as e:
            print('Error creating commit: {}'.format(e))
        os.remove(str(self.__yaml_obj["id"])+'.yml')


class YamlValidator:
    __config_schema = Schema({
        "id": And(str, lambda schema_id: check_for_space(schema_id)),
        "name": str,
        Optional("nick"): And(str, lambda nick: check_for_space(nick)),
        Optional("pronoun"): str,
        Optional("bio"): str,
        Optional("country"): str,
        "avatar": Or(str, bool),
        Optional("position"): str,
        "badges": Or(str, [
            str
        ]),
        "active": bool,
        Optional("openToWork"): bool,
        "projects": Or(str, [
            str
        ]),
        Optional("events"): Or(str, [
            str
        ]),
        Optional("mentor"): Or(str, [
            str
        ]),
        Optional("mentee"): Or(str, [
            str
        ]),
        "social": {
            "gitlab": str,
            Optional("blog"): str,
            Optional("twitter"): str,
            Optional("matrix"): str,
            Optional("instagram"): str,
            Optional("dev_to"): str,
            Optional("github"): str,
            Optional("mastodon"): str,
            Optional("keybase"): str,
        }
    })
    __issue_description = ""

    def __init__(self, issue_description: str):
        self.__issue_description = issue_description

    def validate_yaml(self) -> YamlValidatorReturn:
        try:
            valid_yaml = yaml.safe_load(self.__issue_description)
            return self.__validate_schema(valid_yaml)
        except ScannerError as error:
            print(error)
            message = 'There is a @ symbol in the issues, please remove it.'
            label_t = 'Changes Requested'
            new_comment = YamlValidatorReturn(False, message, label_t, None)
            return new_comment

    def __validate_schema(self, yaml_obj: object) -> YamlValidatorReturn:
        try:
            self.__config_schema.validate(yaml_obj)
            print("Configuration is valid.")
            message = "A merge request has been created for you. Please wait" \
                      "for a moderator to accept your user profile"
            label_t = "Request Created"
            return_obj = YamlValidatorReturn(True, message, label_t, yaml_obj)
            return return_obj
        except SchemaError as se:
            print(se)
            message = "Please follow the template. Error:" + str(se)
            label_t = 'Changes Requested'
            new_comment = YamlValidatorReturn(False, message, label_t, None)
            return new_comment


def check_for_space(tag: str) -> bool:
    if tag.find(" ") == -1:
        return True
    print("Make sure that '" + tag + "' does not contain any whitespace")
    return False


def check_for_at_symbol(tag: str) -> bool:
    if tag.find('@') == -1:
        return True
    print("Make sure that your usernames does not contain the @ symbol")
    return False


if __name__ == '__main__':
    fogbot_labels = ['Profile Request', 'Changes Requested']
    target_project_id = sys.argv[2]

    # There sould be 4 arguments. 1. API Key 2. Project ID 3. Project URL 
    fogbot = GitlabAPIHandler(sys.argv[1],target_project_id, sys.argv[3])
    fogbot_issues = fogbot.create_issue_handler(fogbot_labels)
    fogbot_issues.validate_issues()
    my_issues = fogbot_issues.get_issues()
