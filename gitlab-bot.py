import gitlab
import os
import sys
from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError


class GitlabBot:
    __token = ""
    __url = ""

    def __init__(self, url: str):
        self.gitlab_handler = None
        self.__token = sys.argv[1]
        self.__url = url

    def start(self):
        self.gitlab_handler = GitlabAPIHandler(self.__token, self.__url)
        self.gitlab_handler.connect()


class GitlabAPIHandler:
    _token: str
    _url: str
    _project_id = None

    def __init__(self, token: str, url: str):
        self._client = None
        self._projects = None
        self._token = token
        self._url = url

    def connect(self):
        self._client = gitlab.Gitlab(private_token=self._token, url=self._url)

    def set_project_id(self, project_id):
        self._project_id = project_id

    def create_projects(self):
        self._projects = self._client.projects.get(id=int(self._project_id))

    def get_client(self):
        return self._client

    def create_issue_handler(self, labels: list[str], state='opened', order_by='created_at', sort='desc'):
        if self._client is not None or self._project_id != '':
            return GitlabIssues(self._client, self._project_id, labels, state, order_by, sort)
        else:
            print("Error!")


class GitlabIssues:
    __labels: list[str] = [""]
    __state: str = ""
    __order_by: str = ""
    __sort: str = ""
    __issues = []
    __project_id = ""
    __project = None
    __client = None

    def __init__(self, client, project_id, labels: list[str], state='opened', order_by='created_at', sort='desc'):
        self.__labels = labels
        self.__state = state
        self.__order_by = order_by
        self.__sort = sort
        self.__project_id = project_id
        self.__client = client
        self.__project = self.__client.projects.get(id=int(self.__project_id))

    def request_issues(self):
        self.__issues = self.__project.issues.list(labels=self.__labels,
                                                   state=self.__state,
                                                   order_by=self.__order_by,
                                                   sort=self.__sort)

    def validate_issues(self):
        for issue in self.__issues:
            yaml_result = YamlValidator(issue).validate_yaml(self)
            if yaml_result is not None:
                ref = 'Profile-Request-{}'.format(str(issue.attributes['id']))
                api_token = sys.argv[1]
                mr = GitlabMergeRequest(yaml_result, issue, self.__project, ref, api_token)
                mr.create_merge_request()

    def print_comment(self, issue, message, labels):
        issue_t = self.__project.issues.get(issue.attributes['iid'])
        issue_t.labels = [labels]
        issue_t.notes.create({'body': message})
        issue_t.save()
        print("The issue has been updated")

    def get_issues(self):
        return self.__issues

    def set_labels(self, new_labels: list[str]):
        self.__labels = new_labels

    def get_labels(self):
        return self.__labels


class GitlabMergeRequest:
    __target_branch = 'main'
    __yaml_obj = None
    __issue = None
    __project = None
    __id: str
    __ref_branch: str
    __target_project_id = ""
    __source_project_id = ""

    def __init__(self, yaml_obj, issue, project, source_branch, target_id):
        self.__yaml_obj = yaml_obj
        self.__issue = issue
        self.__project = project
        self.__id = issue.attributes['id']
        self.__source_branch = source_branch
        self.__target_project_id = target_id

    def create_merge_request(self):
        branch = GitlabBranches(self.__project, "main", self.__id)
        if branch.search_for_branch() is not []:
            branch.create_new_branch()
        try:
            commit = GitlabCommits(self.__yaml_obj, self.__project, self.__id)
            data = commit.create_data()
            commit.commit(data)
            self.__project.mergerequests.create({'source_branch': self.__source_branch,
                                                 'target_branch': self.__target_branch,
                                                 'target_project_id': int(self.__target_project_id),
                                                 'source_project_id': int(self.__target_project_id),
                                                 'title': 'Profile request #{}'.format(self.__id)})
        except gitlab.GitlabCreateError as error:
            print(error)

    def retrieve_merge_request(self):
        merge_requests = self.__project.mergerequsts.list()

        for merge_request in merge_requests:
            print(merge_request)

        return merge_requests


class GitlabBranches:
    __project = None
    __ref_branch: str
    __id: str

    def __init__(self, project, ref_branch, issue_id):
        self.__project = project
        self.__ref_branch = ref_branch
        self.__id = issue_id

    def create_new_branch(self) -> bool:
        try:
            self.__project.branches.create({'branch': 'Profile-Request-{}'.format(self.__id),
                                            'ref': self.__ref_branch})
            return True
        except gitlab.GitlabCreateError as error:
            print(error)
            return False

    def search_for_branch(self):
        return self.__project.branches.list(search='Profile-Request-{}'.format(self.__id))


class GitlabCommits:
    __yaml_obj = None
    __project = None

    def __init__(self, yaml_obj, project, issue_id):
        self.__yaml_obj = yaml_obj
        self.__project = project
        self.__issue_id = issue_id

    def create_data(self):
        with open("{}.yml".format(self.__yaml_obj['id']), 'w+') as file:
            yaml.dump(self.__yaml_obj, file)

            return {
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

    def commit(self, data):
        self.__project.commits.create(data)
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
    __issue = None

    def __init__(self, issue):
        self.__issue = issue
        self.__issue_description = issue.attributes['description']

    def validate_yaml(self, gitlab_issue_handler: GitlabIssues):
        try:
            valid_yaml = yaml.safe_load(self.__issue_description)
            return self.__validate_schema(valid_yaml, gitlab_issue_handler)
        except ScannerError as error:
            print(error)
            message = 'There is a @ symbol in the issues, please remove it.'
            label_t = 'Changes Requested'
            gitlab_issue_handler.print_comment(self.__issue, message, label_t)
            return None

    def __validate_schema(self, yaml_obj: object, gitlab_issue_handler: GitlabIssues):
        try:
            self.__config_schema.validate(yaml_obj)
            print("Configuration is valid.")
            message = "A merge request has been created for you. Please wait for a moderator to accept your user " \
                      "profile"
            label_t = "Request Created"
            gitlab_issue_handler.print_comment(self.__issue, message, label_t)
            return yaml_obj
        except SchemaError as se:
            print(se)
            message = str(se)
            label_t = 'Changes Requested'
            gitlab_issue_handler.print_comment(self.__issue, message, label_t)
            return None


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
    print(sys.argv)
    project_id = sys.argv[2]
    fogbot = GitlabBot(url='https://gitlab.com')
    fogbot.start()
    fogbot.gitlab_handler.set_project_id(project_id)
    label = ['Profile Request']
    fogbot_issues = fogbot.gitlab_handler.create_issue_handler(label)
    fogbot_issues.request_issues()
    fogbot_issues.validate_issues()
