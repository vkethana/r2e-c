from paths import REPOS_DIR, LOGGER_DIR
import os
import sys
from utils import *

def run_naive_installation(path):
    config_return_code = os.system(f'cd {path} && ./autogen') # if this command is redundant then it doesnt matter
    config_return_code = os.system(f'cd {path} && ./config') # if the command is redundant then it doesnt matter
    make_return_code = os.system(f'cd {path} && make')
    return make_return_code

def find_makefile(path):
    makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
    for variant in makefile_variants:
        if os.path.isfile(os.path.join(path, variant)):
            return os.path.join(path, variant)
    return None

successes = []
fails = []

for repo_name in os.listdir(REPOS_DIR):
    logger = setup_logger(os.path.join(LOGGER_DIR, repo_name), repo_name)
    repo_path = os.path.join(REPOS_DIR, repo_name)
    logger.info(f"Analyzing {repo_path}")

    makefile_path = find_makefile(repo_path)
    
    # CASE 1: Repo has a makefile
    if makefile_path:
        logger.info(f"Found Makefile: {makefile_path}")
        logger.info("Running naive installation")
        return_code = run_naive_installation(repo_path)
        if return_code != 0:
            logger.error(f"Error: make failed for {repo_name}")
            fails.append(repo_name)
        else:
            logger.info(f"Success: make succeeded for {repo_name}")
            successes.append(repo_name)
    else:
        logger.error(f"No Makefile found for {repo_name}")
        fails.append(repo_name)

    # TODO: Case 2: Repo has a CMakeLists.txt
    # TODO: Case 3: Repo has a configure script
    # TODO: Case 4: Repo has gradlew files

print("Successes:")
print(successes)
print("Fails:")
print(fails)
print("Total number of repos:")
print(len(successes) + len(fails))
print("Number of successes:")
print(len(successes))
print("Number of fails:")
print(len(fails))
