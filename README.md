 # FOG-Bot
This project contains the code for the markdown bot for the Faces of Gnome project. The script vaildates gitlabs issues with "profile request". The script vaildates that the issue follows a [template](https://gitlab.gnome.org/Teams/Engagement/websites/people-of-gnome/-/blob/master/_data/member-template.yml). The script can be stored inside a repo and triggered using Gitlab's CI/CD.

## Installation
1. Upload gitlab-bot.py to your Gitlab repo.
2. Insert process issues 
3. First go to <b>Settings / CI/CD / Pipeline triggers / add trigger</b>. This will create a token.
4. Then copy the webhook url at the bottom of the page and replace TOKEN with the token you just got from above. Replace REF with the branch where the bot is stored. It should look like this:
```
https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/ref/REF/trigger/pipeline?token=TOKEN&variables[ISSUE_BOT]=true
```
5. Then go to <b>Settings/ Webhooks</b> and create a new webhook with the issues event selected. Use the Url you created in the last step.
6. Test it by by clicking on the test button on your webhook and click on "issue event". If this is setup correctly then a new job should be started called proccess_issue.

## License
This project is licensed under the Creative Commons BY-SA-4.0. Press the link to view the [licence](https://github.com/PanicAtTheKernal/fog-bot/blob/main/LICENCE)
