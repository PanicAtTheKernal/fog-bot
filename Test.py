import gitlab
import gitlab.v4.objects.projects
import os
import sys
from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError


class GitlabBot:
    """This creates a client to access the Gitlab API

    Returns:
        gitlab.Gitlab: A gitlab client used for access to the API
    """
    _token: str
    _url: str
    _client: gitlab.Gitlab

    def __init__(self):
        self.gitlab_handler = None
        self._token = sys.argv[1]
        self._url = sys.argv[3]
        self.start()

    def start(self) -> None:
        self._client = gitlab.Gitlab(private_token=self._token, url=self._url)

    def get_client(self) -> gitlab.Gitlab:
        return self._client


class GitlabAPIHandler(GitlabBot):
    _project_id: str
    _project: gitlab.v4.objects.projects.Project

    def __init__(self, project_id: str):
        super().__init__()
        self._project_id = project_id

    def get_project_id(self) -> str:
        return self._project_id

    def retrive_project(self) -> None:
        self._project = self._client.projects.get(id=int(self._project_id))
        a = type(self._project)
        print(a)


if __name__ == "__main__":
    if len(sys.argv) == 4:
        test = GitlabAPIHandler(sys.argv[2])
        test.retrive_project()
        # print(gitlab.__annotations__)
    else:
        print("Argv is less than 4")
