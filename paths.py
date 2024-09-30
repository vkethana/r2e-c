import os
import time

CLONED_REPO_ID = "repos_400_c_round_two" # don't change this unless you want to test a different set of cloned repo
TEST_ID = "with_manual_installation_of_missing_packages" # you can change this
REPOS_DIR = f'repos/'
LOGGER_DIR = f'logs/{CLONED_REPO_ID}_{TEST_ID}_{time.strftime("%Y-%m-%d_%H-%M-%S")}'
REPO_LIST = 'repos500.json'

# Check if REPORS_DIR exists
if not os.path.exists(REPOS_DIR):
    # If not, create it
    os.makedirs(REPOS_DIR)

if not os.path.exists(LOGGER_DIR):
    os.makedirs(LOGGER_DIR)
