import os
import time

CLONED_REPO_ID = "repos_10" # don't change this unless you want to test a different set of cloned repo
TEST_ID = "second_try" # you can change this
REPOS_DIR = f'repos/{CLONED_REPO_ID}'
LOGGER_DIR = f'logs/{CLONED_REPO_ID}_{TEST_ID}_{time.strftime("%Y-%m-%d_%H-%M-%S")}'
REPO_LIST = 'json/repos_easy_10.json'
SELF_EQUIV_OUTPUT_DIR = f"self_equiv_tests/{CLONED_REPO_ID}_{TEST_ID}"

directories = [REPOS_DIR, LOGGER_DIR, SELF_EQUIV_OUTPUT_DIR, 'json', SELF_EQUIV_OUTPUT_DIR]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
