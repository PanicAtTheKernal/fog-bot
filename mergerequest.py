import random

import gitlab
import os
from dotenv import load_dotenv
from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError


def login_to_gitlab():
    load_dotenv()
    gl_t = gitlab.Gitlab(private_token=os.getenv('BOTTOKEN'), url='https://gitlab.com')
    return gl_t


def get_current_issues(gl):
    project = gl.projects.get(id=os.getenv('BOTPROJECT'))
    issues = project.issues.list(labels=['Profile Request'], state='opened', order_by='created_at', sort='desc')
    return issues[0].attributes['description']


if __name__ == '__main__':
    gl = login_to_gitlab()
    pro = gl.projects.get(id=os.getenv())
     # conf_yaml = """
     #    id: test5
     #    name: Jane Doe
     #    nick: Elsadfh
     #    pronoun: she/her
     #    bio: I'm the best in the world lol
     #    country: 🤴🏿
     #    avatar: none
     #    badges: contributor
     #    social:
     #        gitlab: gamerEpic445
     #    """
    # try:
        # configuration = yaml.safe_load(conf_yaml)
        # id_yaml = configuration["id"]
        # project = gl.projects.get(id=os.getenv('BOTPROJECT'))
        # project_user = gl.projects.get(id=os.getenv('USERPROJECT'))

        # debug
    #     for merge_request in project_user.mergerequests.list():
    #         print(merge_request)
    #     try:
    #         branch = project.branches.create({'branch': '{}'.format(id_yaml),
    #                                           'ref': 'Empty'})
    #     except gitlab.GitlabCreateError:
    #         print("Branch exists")
    #
    #     file = open("{}.yml".format(id_yaml), "w")
    #     yaml.dump(configuration, file)
    #     file.close()
    #
    #     data = {
    #         'branch': '{}'.format(id_yaml),
    #         'commit_message': 'Commit for profile request {}'.format("THE ID OF THE ISSUE"),
    #         'actions': [
    #             {
    #                 'action': 'create',
    #                 'file_path': '{}.yml'.format(configuration["id"]),
    #                 'content': open('{}.yml'.format(configuration["id"])).read(),
    #             }
    #         ]
    #     }
    #     commit = project.commits.create(data)
    #     os.remove(str(id_yaml)+'.yml')
    #
    #     try:
    #         mr = project.mergerequests.create({'source_branch': str(id_yaml),
    #                                            'target_branch': 'main',
    #                                            'target_project_id': int(os.getenv('USERPROJECT')),
    #                                            'source_project_id': int(os.getenv('BOTPROJECT')),
    #                                            'title': 'Profile request {}'.format(random.randint(0, 100))})
    #     except gitlab.GitlabCreateError:
    #         print("A merge request already exists")
    # except ScannerError as error:
    #     print(error)




