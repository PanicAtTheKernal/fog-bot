import gitlab
import os
from dotenv import load_dotenv
from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError


class GitlabBot:
    __token = ""
    __url = ""

    def __init__(self, token_name: str, url: str):
        load_dotenv()
        self.__token = os.getenv(token_name)
        self.__url = url

    def start(self):
        gitlab_handler = GitlabAPIHandler(self.__token, self.__url)
        gitlab_handler.connect()
        return gitlab_handler


class GitlabAPIHandler:
    _token: str
    _url: str
    _client = None
    _project_id = None

    def __init__(self, token: str, url: str):
        self._token = token
        self._url = url

    def connect(self):
        self._client = gitlab.Gitlab(private_token=self._token, url=self._url)

    def set_project_id(self, project_id):
        self._project_id = project_id

    def get_client(self):
        return self._client

    def create_issue_handler(self, labels: [str], state='opened', order_by='created_at', sort='desc'):
        if self._client is not None:
            return GitlabIssues(self._client, self._project_id, labels, state, order_by, sort)


class GitlabIssues:
    __labels: [str] = [""]
    __state: str = ""
    __order_by: str = ""
    __sort: str = ""
    __issues = []
    __project_id = ""
    __project = None
    __client = None

    def __init__(self, client, project_id, labels: [str], state='opened', order_by='created_at', sort='desc'):
        self.__labels = labels
        self.__state = state
        self.__order_by = order_by
        self.__sort = sort
        self.__project_id = project_id
        self.__client = client

    def request_issues(self):
        if self.__project is not None:
            self.__project = self.__client.project.get(id=self.__project_id)
        self.__issues = self.__project.issues.list(labels=self.__labels,
                                                   state=self.__state,
                                                   order_by=self.__order_by,
                                                   sort=self.__sort)

    def validate_issues(self):
        for issue in self.__issues:
            YamlValidator(issue).validate_yaml(self)

    def print_comment(self, issue, message, labels):
        issue_t = self.__project.issues.get(issue.attributes['iid'])
        issue_t.labels = [labels]
        issue_t.notes.create({'body': message})
        issue_t.save()
        print("The issue has been updated")

    def get_issues(self):
        return self.__issues

    def set_labels(self, new_labels: [str]):
        self.__labels = new_labels

    def get_labels(self):
        return self.__labels


class GitlabMergeRequest:
    __ref_branch = 'main'
    __target_branch = 'main'
    __yaml_obj = None
    __issue = None

    def __init__(self, yaml_obj, issue):
        self.__yaml_obj = yaml_obj
        self.__issue = issue

    def create_merge_request(self):
        pass

    def create_new_branch(self):
        pass

    def create_data(self):
        file = open("{}.yml".format(self.__yaml_obj['id']))
        yaml.dump(self.__yaml_obj, file)
        file.close()

        data = {
            'branch': '{}'.format(self.__yaml_obj['id']),
            'commit_message': 'Commit for profile request {}'.format(self.__issue["id"]),
            'actions': [
                {
                    'action': 'create',
                    'file_path': '{}.yml'.format(self.__yaml_obj['id']),
                    'content': open('{}.yml'.format(self.__yaml_obj['id'])).read(),
                }
            ]
        }

        return data


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

    def validate_yaml(self, gitlab_issue_handler: GitlabIssues)-> bool:
        try:
            valid_yaml = yaml.safe_load(self.__issue_description)
            return self.__validate_schema(valid_yaml, gitlab_issue_handler)
        except ScannerError as error:
            print(error)
            message = 'There is a @ symbol in the issues, please remove it.'
            label = 'Changes Requested'
            gitlab_issue_handler.print_comment(self.__issue, message, label)
            return False

    def __validate_schema(self, yaml_obj: object, gitlab_issue_handler: GitlabIssues)-> bool:
        try:
            self.__config_schema.validate(yaml_obj)
            print("Configuration is valid.")
            message = "A merge request has been created for you. Please wait for a moderator to accept your user " \
                      "profile"
            label = "Request created"
            gitlab_issue_handler.print_comment(self.__issue, message, label)
            return True
        except SchemaError as se:
            print(se)
            message = str(se)
            label = 'Changes Requested'
            gitlab_issue_handler.print_comment(self.__issue, message, label)
            return False


def check_for_space( tag: str) -> bool:
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
    pass
