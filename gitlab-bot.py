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
        gitlab_handler = GitlabHandler(self.__token, self.__url)
        gitlab_handler.connect()
        return gitlab_handler


class GitlabHandler:
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

    def create_issue_handler(self, labels: [str], state: [str], order_by: str, sort: str):
        if self._client != None:



class GitlabIssues:
    __labels: [str] = [""]
    __state: str = ""
    __order_by: str = ""
    __sort: str = ""
    __issues = []
    __project_id = ""
    __project = None

    def __init__(self, project_id, labels: [str], state='opened', order_by='created_at', sort='desc'):
        self.__labels = labels
        self.__state = state
        self.__order_by = order_by
        self.__sort = sort
        self.__project_id = project_id

    def request_issues(self, client):
        if self.__project is None:
            self.__project = client.project.get(id=self.__project_id)
        self.__issues = self.__project.issues.list(labels=self.__labels,
                                                   state=self.__state,
                                                   order_by=self.__order_by,
                                                   sort=self.__sort)

    def get_issues(self):
        return self.__issues

    def set_labels(self, new_labels: [str]):
        self.__labels = new_labels

    def get_labels(self):
        return self.__labels

class GitlabMergeRequest:
    pass


class YamlValidator:
    pass


def login_to_gitlab():
    load_dotenv()
    gl = gitlab.Gitlab(private_token=os.getenv('BOTTOKEN'), url='https://gitlab.com')
    get_current_issues(gl)


def get_current_issues(gl):
    project = gl.projects.get(id=33046772)
    issues = project.issues.list(labels=['Profile Request'], state='opened', order_by='created_at', sort='desc')
    validate_yaml(issues[0], project)
    print(issues[0].attributes['description'])


def validate_yaml(issue, project):
    config_schema = Schema({
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

    try:
        configuration = yaml.safe_load(issue.attributes['description'])
        try:
            config_schema.validate(configuration)
            print("Configuration is valid.")
            message = "A merge request has been created for you. Please wait for a moderator to accept your user profile"
            label = "Request created"
            print_note(issue, project, message, label)
        except SchemaError as se:
            print(se)
            message = str(se)
            label = 'Changes Requested'
            print_note(issue, project, message, label)
    except ScannerError as error:
        print(error)
        message = 'There is a @ symbol in the issues, please remove it.'
        label = 'Changes Requested'
        print_note(issue, project, message, label)

def create_merge_request():
    pass

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


def print_note(issue, project, message: str, label: str):
    issue_t = project.issues.get(issue.attributes['iid'])
    issue_t.labels = [label]
    issue_t.save()
    response = issue_t.notes.create({'body': message})
    print(response)


if __name__ == '__main__':
    login_to_gitlab()

    # projects = gl.projects.list(owned=True)
    # for project in projects:
    #     print(project)

    # Requires an admin token to create a user.
    # user = gl.users.create({'email': 'markdownbot@botemail.com',
    #                         'password': 'Mark@IT*down',
    #                         'username': 'MarkdownBot',
    #                         'name': 'Markdown Bot'})

    # gitlab_token = user.impersonationtokens.create({'name': 'token1', 'scopes': ['api']})
    # user_gl = gitlab.Gitlab(private_token=gitlab_token.token, url='https://gitlab.com')

    # response = issue.notes.create({'body': 'I\'m a bot and this is my response'})

    # print(issues)

    # user.delete()
_