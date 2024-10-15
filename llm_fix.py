import os
import subprocess
import json
from openai import OpenAI
from utils import setup_logger
from paths import REPOS_DIR

# Docker container name
CONTAINER_NAME = "test_80_easy_2_container"

# Directory on the Docker container for logs
DOCKER_LOGS_DIR = "/INSTALL_C/logs/repos_400_c_round_two_with_manual_installation_of_missing_packages_2024-10-07_00-38-25"

# Local directory to store logs
LOCAL_LOGS_DIR = "./local_logs"

# Maximum attempts to rebuild
MAX_ATTEMPTS = 5


def copy_from_docker(container_name, docker_path, local_path):
    """
    Copy log files from a Docker container to the local system.
    """
    if not os.path.exists(local_path):
        os.makedirs(local_path)
        print(f"Created local directory: {local_path}")

    print(f"Attempting to copy logs from {docker_path} in container {container_name} to {local_path}")

    cmd = f"docker cp {container_name}:{docker_path} {local_path}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Error: Failed to copy files from {docker_path} in container {container_name}.")
        print(f"Error message: {result.stderr.decode()}")
        raise Exception(f"Failed to copy files from {docker_path} in container {container_name}. Error: {result.stderr.decode()}")
    else:
        print(f"Successfully copied files from {docker_path} in container {container_name} to {local_path}.")
        print(f"Output: {result.stdout.decode()}")

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


def attempt_rebuild(repo_name, log_content, logger):
    """
    Attempt to rebuild the repository based on log content and GPT-4 suggestions.
    """
    last_command = "Initial setup"
    last_output = "Log analysis"
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info(f"Attempt {attempt}: Rebuilding repo '{repo_name}'")

        # Ask GPT-4 for a fix based on log content
        suggested_fix = llm_suggest_fix(log_content, last_command, last_output)
        logger.info(f"Suggested fix from GPT-4: {suggested_fix}")

        # Simulate execution of the suggested command (replace this with actual rebuild if needed)
        result = subprocess.run(suggested_fix, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode() + result.stderr.decode()

        if result.returncode == 0:
            logger.info(f"Build succeeded on attempt {attempt}.")
            return True  # Success

        logger.error(f"Build failed on attempt {attempt}. Output:\n{output}")
        write_failure_log(repo_name, suggested_fix, output)

        last_command = suggested_fix
        last_output = output

    logger.error(f"Build failed after {MAX_ATTEMPTS} attempts for repo '{repo_name}'")
    return False  # Failure


def main():
    # Set up logger
    logger = setup_logger('logs', 'llm_fix')

    # Copy log files from Docker container to local system
    copy_from_docker(CONTAINER_NAME, DOCKER_LOGS_DIR, LOCAL_LOGS_DIR)

    # Go through each log file
    for log_file in os.listdir(LOCAL_LOGS_DIR):
        log_file_path = os.path.join(LOCAL_LOGS_DIR, log_file)

        # Extract repo name from log file
        repo_name = log_file.replace('_build.log', '')

        logger.info(f"Processing log for repo '{repo_name}'")

        # Read the log file content
        with open(log_file_path, 'r') as file:
            log_content = file.read()

        if log_content:
            logger.info(f"Log content retrieved for repo '{repo_name}'. Attempting to rebuild.")
            success = attempt_rebuild(repo_name, log_content, logger)
            if not success:
                logger.error(f"Marking repo '{repo_name}' as failed after {MAX_ATTEMPTS} attempts.")
        else:
            logger.info(f"No log content found for repo '{repo_name}'.")


if __name__ == "__main__":
    main()



