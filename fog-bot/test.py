from schema import Optional, And, Or, Schema, SchemaError
import yaml
from yaml.scanner import ScannerError

"""
id: epic-user
name: John Doe
nick: Epicprogramer777
pronoun: he/him
bio: Like stuff Hate stuff
country: 🏴‍☠️
avatar: none
position: Contributor
badges: contributor
active: true
openToWork: true
projects: 
  - gtk 
  - gnome-shell
events: #refer: events.json for conference ids
  - guadec-2021
  - gnsummit-2015
mentor: #GSoC/Outreachy mentors
  - gsoc-2021 
  - gsoc-2020 
  - outreachy-2019
mentee: #GSoC/Outreachy students
  - gsoc-2021 
  - gsoc-2020 
  - outreachy-2019
social:
  blog: https://my.site
  twitter: handle
  gitlab: handle
  matrix: handle #don't include @
  instagram: handle
  dev_to: handle
  github: handle
  mastodon: handle #don't include @
  keybase: handle
"""


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


def name_validator(full_name: str) -> bool:
    name_arr = full_name.split()
    if len(name_arr) != 2:
        return False
    for name in name_arr:
        if name != name.capitalize():
            return False
    return True


if __name__ == '__main__':
    current_errors = []

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

    conf_yaml = """
    id: test
    name: John Doe
    nick: Epicgamer123
    pronoun: he/him
    bio: I'm the best in the world lol
    country: 🤴🏿
    avatar: none
    badges: contributor
    social: 
        gitlab: @gamerEpic445
    """

    try:
        configuration = yaml.safe_load(conf_yaml)
    except ScannerError as error:
        print(error)

    try:
        config_schema.validate(configuration)
        print("Configuration is valid.")
    except SchemaError as se:
        print(se)
