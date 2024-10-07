import os
import openai
import docker
import subprocess
from utils import setup_logger
from paths import REPOS_DIR
from openai import OpenAI



def copy_log_from_docker(container_name: str, log_file_path: str, local_dir: str) -> str:
    """
    Copy the log file from the Docker container to a local directory.
    """
    # Define the local log file path
    local_log_file_path = os.path.join(local_dir, os.path.basename(log_file_path))

    # Use docker cp to copy log from container to local system
    cmd = f"docker cp {container_name}:{log_file_path} {local_log_file_path}"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise Exception(f"Error copying log file from container: {result.stderr}")
    
    return local_log_file_path

def read_local_log_content(log_file_path: str) -> str:
    """
    Read the content of a local log file.
    """
    with open(log_file_path, 'r') as file:
        return file.read()

def request_fix_from_llm(repo_name: str, log_content: str, attempt: int) -> str:
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    client = docker.from_env()
    if not openai_client.api_key:
        raise EnvironmentError("Please set the OPENAI_API_KEY environment variable.")
    """Request GPT-4 Turbo to suggest fixes based on log content."""
    msg_content = f"Repo: {repo_name}\nLog content:\n{log_content}\nAttempt: {attempt}/5.\nPlease suggest a fix to resolve the issues and rebuild the repo."

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping to complete the installation process of a repo that failed during building."},
            {"role": "user", "content": msg_content}
        ]
    )

    return response.choices[0].message.content.strip().replace("```bash", "").replace("`", "").replace("\n", "")


def attempt_rebuild_in_docker(container_name: str, repo_path: str, log_content: str, logger):
    """Attempt to rebuild the repo in the Docker container up to 5 times using log content as context."""
    for attempt in range(1, 6):  # Upper limit of 5 trials
        logger.info(f"Attempt {attempt}: Rebuilding repo '{os.path.basename(repo_path)}' inside container '{container_name}' based on log content.")

        fix_suggestion = request_fix_from_llm(os.path.basename(repo_path), log_content, attempt)
        logger.info(f"GPT suggested fix: {fix_suggestion}")

        # Execute the fix inside the container
        cmd = f"docker exec {container_name} bash -c '{fix_suggestion}'"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            logger.error(f"Fix attempt failed: {result.stderr}")
        else:
            logger.info(f"Fix applied: {result.stdout}")

        # Rebuild repo inside container
        rebuild_cmd = f"docker exec {container_name} bash -c 'cd {repo_path} && make clean && make'"
        logger.info(f"Running rebuild command: {rebuild_cmd}")
        rebuild_result = subprocess.run(rebuild_cmd, shell=True)

        if rebuild_result.returncode == 0:
            logger.info(f"Build succeeded for repo '{os.path.basename(repo_path)}' on attempt {attempt}.")
            return True 
        else:
            logger.error(f"Build failed for repo '{os.path.basename(repo_path)}' on attempt {attempt}.")

    logger.error(f"Failed to rebuild repo '{os.path.basename(repo_path)}' after 5 attempts.")
    return False  

def main():
    # TODO: Hardcoded log directory and container name. Change this later
    LOGS_DIR = "/INSTALL_C/logs/repos_400_c_round_two_with_manual_installation_of_missing_packages_2024-10-07_00-38-25"
    LOCAL_LOG_DIR = "./local_logs"  # Local directory to store logs
    os.makedirs(LOCAL_LOG_DIR, exist_ok=True)  # Ensure local log directory exists

    logger = setup_logger(LOCAL_LOG_DIR, 'llm_fix')  # Using LOCAL_LOG_DIR for logging
    container_name = "test_80_easy_2_container"

    # Iterate over repositories
    for repo_name in os.listdir(REPOS_DIR):
        repo_path = os.path.join(REPOS_DIR, repo_name)
        log_file_path = os.path.join(LOGS_DIR, f"{repo_name}_build.log")

        if not log_file_path.endswith('_build.log'):
            continue

        # Copy log file from Docker container to local machine
        logger.info(f"Copying log for repo '{repo_name}' from container '{container_name}'.")
        try:
            local_log_path = copy_log_from_docker(container_name, log_file_path, LOCAL_LOG_DIR)
        except Exception as e:
            logger.error(f"Error copying log file for '{repo_name}': {str(e)}")
            continue

        # Read the copied local log file content
        log_content = read_local_log_content(local_log_path)
        
        if log_content:
            logger.info(f"Log content retrieved for repo '{repo_name}'. Initiating rebuild process.")
            success = attempt_rebuild_in_docker(container_name, repo_path, log_content, logger)
            if not success:
                logger.error(f"Marking repo '{repo_name}' as failed after 5 attempts.")
        else:
            logger.info(f"No log content found for repo '{repo_name}'.")

if __name__ == "__main__":
    main()
