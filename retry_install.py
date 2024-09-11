import os
import subprocess
from typing import List, Dict, Tuple
from install_repos import build_repo  # Assuming your existing code is in a file called build_script.py
from utils import setup_logger  # Assumed to be available from your original script
from paths import REPOS_DIR, LOGGER_DIR  # Assumed to be available from your original script

# Set number of retries for each missing header issue
num_tries = 3  # You can modify this variable as needed

class StatsTracker:
    def __init__(self):
        self.successes = 0
        self.failures = 0
        self.total_repos = 0
        self.build_system_counts = {
            "MakefileBuildSystem": {"success": 0, "total": 0},
            "AutotoolsBuildSystem": {"success": 0, "total": 0},
            "CMakeBuildSystem": {"success": 0, "total": 0},
            "GradleBuildSystem": {"success": 0, "total": 0},
            "Unknown": {"success": 0, "total": 0},
        }
        self.missing_headers = set()
        self.no_build_system = 0
        self.package_not_found = 0
        self.configure_errors = 0
        self.other_errors = 0

    def update_stats(self, build_system: str, result: bool, missing_headers: List[str], error_type: str):
        self.total_repos += 1
        self.build_system_counts[build_system]["total"] += 1

        if result:
            self.successes += 1
            self.build_system_counts[build_system]["success"] += 1
        else:
            self.failures += 1
            if error_type == "missing_header":
                self.missing_headers.update(missing_headers)
            elif error_type == "no_build_system":
                self.no_build_system += 1
            elif error_type == "package_not_found":
                self.package_not_found += 1
            elif error_type == "configure_error":
                self.configure_errors += 1
            else:
                self.other_errors += 1

    def print_stats(self):
        # Begin green color
        print("\033[92m")
        print(f"Overall success rate: {self.successes}/{self.total_repos}")
        for system, counts in self.build_system_counts.items():
            print(f"Success rate for {system} Repos: {counts['success']}/{counts['total']}")
        print(f"Number of repos with no detectable build system: {self.no_build_system}")
        print(f"Number of repos with package not found error: {self.package_not_found}")
        print(f"Number of repos with ./configure errors: {self.configure_errors}")
        print(f"Number of repos with other errors: {self.other_errors}")
        print(f"List of all missing headers so far: {sorted(self.missing_headers)}")

        # End green color
        print("\033[00m")

def get_package_name(header: str) -> str:
    """
    Suggests a package name based on the missing header file.
    Args:
        header (str): The header file name (e.g., 'bfd.h').

    Returns:
        str: Suggested package name (e.g., 'libbfd-dev').
    """
    # Strip potential directory paths and file extensions
    header_name = header.split('/')[-1].replace('.h', '')

    # Heuristics to map headers to likely package names
    # ChatGPT gives some example hardcoded mappings, but I prefer to not use hardcoded package mappings
    header_to_package_map = {} 
    '''{
        'bfd': 'libbfd-dev',
        'gmp': 'libgmp-dev',
        'ev': 'libev-dev',
        'lua': 'liblua5.3-dev',  # Adjust version as needed
        'avcodec': 'libavcodec-dev',
        'osdef': 'libxosd-dev',  # Example heuristic, adjust if necessary
        'c++-config': 'libstdc++-dev',  # Common C++ header
        'sys/capability': 'libcap-dev',  # For sys/capability.h
        'bits': 'libc6-dev',  # For bits headers commonly found in libc
    }
    '''
    # Commented out because hardcoded package mappings aren't sustainable or scalable in the long run

    # Check for exact matches first
    if header_name in header_to_package_map:
        return header_to_package_map[header_name]

    # Apply general heuristic
    return f"lib{header_name}-dev"

def install_missing_headers(missing_headers: List[str], logger) -> bool:
    """
    Attempt to install missing headers using apt-get.

    Returns True if all headers were installed successfully, False otherwise.
    """
    all_installed = True
    for header in missing_headers:
        package_name = get_package_name(header)
        if not package_name:
            logger.error(f"Could not find package for header: {header}")
            all_installed = False
            continue

        logger.info(f"Attempting to install package: {package_name} for missing header: {header}")
        result = subprocess.run(['sudo', 'apt-get', 'install', '-y', package_name],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            logger.error(f"Failed to install {package_name}: {result.stderr.decode()}")
            all_installed = False
        else:
            logger.info(f"Successfully installed {package_name}")

    return all_installed

def retry_build(repo_path: str, logger, stats: StatsTracker, max_retries: int = num_tries):
    """
    Attempt to build the repo, retrying up to max_retries times if missing header errors occur.
    """
    build_system, result, missing_headers, output = build_repo(repo_path, logger)
    error_type = "other"

    retries = 0
    while missing_headers and retries < max_retries:
        logger.info(f"Attempt {retries + 1}/{max_retries} to fix missing headers: {missing_headers}")
        error_type = "missing_header"
        if not install_missing_headers(missing_headers, logger):
            logger.error("Failed to resolve missing headers. Aborting retries.")
            break

        logger.info("Retrying build...")
        build_system, result, missing_headers, output = build_repo(repo_path, logger)
        retries += 1

    if missing_headers:
        logger.error(f"Build failed after {retries} retries due to unresolved missing headers: {missing_headers}")
        # Print in red color
        print(f"\033[91mBuild failed after {retries} retries due to unresolved missing headers: {missing_headers}\033[00m")
    else:
        logger.info(f"Build completed successfully after {retries} retries.")
        # Print in green color
        print(f"\033[92mBuild completed successfully after {retries} retries.\033[00m")

    # Update stats with the results of the build attempt
    stats.update_stats(build_system, result, missing_headers, error_type)

def main():
    # Initialize stats tracker
    stats = StatsTracker()

    # Iterate over repositories in REPOS_DIR
    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(LOGGER_DIR, repo_name)
        repo_path = os.path.join(REPOS_DIR, repo_name)
        logger.info(f"Analyzing {repo_path}")

        # Run the retry build process
        retry_build(repo_path, logger, stats, max_retries=num_tries)
        stats.print_stats()

    # Print the running statistics at the end
    stats.print_stats()

if __name__ == "__main__":
    main()

