import os
import subprocess
import json
from openai import OpenAI
from utils import setup_logger

# Docker container name
CONTAINER_NAME = "test_80_easy_2_container"

# Directories on the Docker container
DOCKER_LOGS_DIR = "/INSTALL_C/logs/repos_400_c_round_two_with_manual_installation_of_missing_packages_2024-10-07_00-38-25"
DOCKER_REPOS_DIR = "/INSTALL_C/repos"

# Local directories
LOCAL_LOGS_DIR = "./local_logs"
LOCAL_REPOS_DIR = "./local_repos"

# Maximum attempts to rebuild
MAX_ATTEMPTS = 5

def copy_from_docker(container_name, docker_path, local_path):
    """
    Copy files from a Docker container to the local system.
    """
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    cmd = f"docker cp {container_name}:{docker_path} {local_path}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise Exception(f"Failed to copy files from {docker_path} in container {container_name}. Error: {result.stderr.decode()}")
    else:
        print(f"Copied files from {docker_path} in container {container_name} to {local_path}.")

def write_failure_log(image_name, command, output):
    """
    Write failure logs to a file named <image_name>_failures.json
    """
    if not os.path.exists("failures"):
        os.makedirs("failures")

    failure_log_path = f"failures/{image_name}_failures.json"
    with open(failure_log_path, "a") as f:
        f.write(json.dumps({
            "command": command,
            "output": output
        }) + "\n")


def llm_suggest_fix(log_content, last_command, last_output):
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    """
    Use GPT-4 to suggest the next fix based on log content.
    """
    msg_content = f"""
    Log content:\n{log_content}
    Last command executed: {last_command}
    Output/Error: {last_output}

    - Suggest the next command to try and fix the errors in the log.
    """
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping to resolve build errors."},
            {"role": "user", "content": msg_content}
        ]
    )
    return response.choices[0].message.content.strip().replace("```bash", "").replace("`", "").replace("\n", "")

def attempt_rebuild(repo_path, log_content, logger):
    """
    Attempt to rebuild the repository based on log content and GPT-4 suggestions.
    """
    last_command = "Initial setup"
    last_output = "Log analysis"
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info(f"Attempt {attempt}: Rebuilding repo at '{repo_path}'")

        # Ask GPT-4 for a fix based on log content
        suggested_fix = llm_suggest_fix(log_content, last_command, last_output)
        logger.info(f"Suggested fix from GPT-4: {suggested_fix}")

        # Execute the suggested command
        bash_command = f"cd {repo_path} && {suggested_fix}"
        result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode() + result.stderr.decode()

        if result.returncode == 0:
            logger.info(f"Build succeeded on attempt {attempt}.")
            return True  # Success

        logger.error(f"Build failed on attempt {attempt}. Output:\n{output}")
        write_failure_log(repo_path, bash_command, output)

        last_command = bash_command
        last_output = output

    logger.error(f"Build failed after {MAX_ATTEMPTS} attempts for repo at '{repo_path}'")
    return False  # Failure


def main():
    # Set up logger
    logger = setup_logger('logs', 'llm_fix')

    # Copy log and repo files from Docker container to local system
    copy_from_docker(CONTAINER_NAME, DOCKER_LOGS_DIR, LOCAL_LOGS_DIR)
    copy_from_docker(CONTAINER_NAME, DOCKER_REPOS_DIR, LOCAL_REPOS_DIR)

    # Go through each repository's log file
    for repo_name in os.listdir(LOCAL_REPOS_DIR):
        repo_path = os.path.join(LOCAL_REPOS_DIR, repo_name)
        log_file_path = os.path.join(LOCAL_LOGS_DIR, f"{repo_name}_build.log")

        if not os.path.exists(log_file_path):
            continue  # Skip if no log file exists for this repo

        logger.info(f"Processing log for repo '{repo_name}'")

        # Read the log file content
        with open(log_file_path, 'r') as log_file:
            log_content = log_file.read()

        if log_content:
            logger.info(f"Log content retrieved for repo '{repo_name}'. Attempting to rebuild.")
            success = attempt_rebuild(repo_path, log_content, logger)
            if not success:
                logger.error(f"Marking repo '{repo_name}' as failed after {MAX_ATTEMPTS} attempts.")
        else:
            logger.info(f"No log content found for repo '{repo_name}'.")


if __name__ == "__main__":
    main()


