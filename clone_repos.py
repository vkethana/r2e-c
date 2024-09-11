import json
import os
from paths import REPOS_DIR, REPO_LIST

# Get path to repo list
with open(REPO_LIST) as f:
    # Load the json data into a variable called repos
    repos = json.load(f)

    # Make sure repos is a list
    assert isinstance(repos, list)

# Run git clone on each repo in the list
for repo in repos:
    # Get repo prefix
    repo_prefix = "https://github.com/"

    # Get repo author
    author = repo[len(repo_prefix):].split('/')[0]

    # Get repo name
    name = repo[len(repo_prefix):].split('/')[1]

    # Get repo id
    repo_id = "{}___{}".format(author, name)

    # Run git clone on the repo
    os.system('git clone ' + repo + ".git" + " " + REPOS_DIR + "/" + repo_id)
