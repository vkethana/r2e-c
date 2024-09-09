from abc import ABC, abstractmethod
import os
from typing import List, Tuple
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger
import logging
import subprocess

class BuildSystem(ABC):
    @abstractmethod 
    def detect(self, repo_path: str) -> bool:
        pass

    @abstractmethod
    def build(self, repo_path: str, logger):
        pass

    def run_command(self, command: str, repo_path: str, logger) -> bool:
        log_file = os.path.join(LOGGER_DIR, f"{os.path.basename(repo_path)}_build.log")
        logger.info(f"Running command: {command}")
        logger.info(f"Logging output to: {log_file}")
        
        with open(log_file, 'a') as log:
            log.write(f"Running command: {command}\n")
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            for line in process.stdout:
                log.write(line)
                logger.debug(line.strip())
            
            return_code = process.wait()
            log.write(f"Command finished with return code: {return_code}\n\n")
            
        return return_code == 0

class MavenBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'pom.xml'))

    def build(self, repo_path: str, logger):
        logger.info("Running Maven clean and build")
        self.run_command('mvn clean', repo_path, logger)
        if not self.run_command('mvn install', repo_path, logger):
            return "maven build failed"
        return "success"

class GradleBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.gradle')) or os.path.isfile(os.path.join(repo_path, 'gradlew'))

    def build(self, repo_path: str, logger):
        logger.info("Running Gradle clean and build")
        self.run_command('./gradlew clean', repo_path, logger)
        if not self.run_command('./gradlew build', repo_path, logger):
            return "gradle build failed"
        return "success"

class AntBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.xml'))

    def build(self, repo_path: str, logger):
        logger.info("Running Ant clean and build")
        self.run_command('ant clean', repo_path, logger)
        if not self.run_command('ant', repo_path, logger):
            return "ant build failed"
        return "success"

def build_repo(repo_path: str, logger):
    build_systems = [
        MavenBuildSystem(),
        GradleBuildSystem(),
        AntBuildSystem(),
    ]

    repo_name = os.path.basename(os.path.normpath(repo_path))
    possible_subdirs = [
        "src",
        "Source",
        os.path.join(repo_name, "src")
    ]

    for build_system in build_systems:
        if build_system.detect(repo_path):
            return build_system.build(repo_path, logger)
        else:
            for subdir in possible_subdirs:
                    subdir_path = os.path.join(repo_path, subdir)
                    if os.path.exists(subdir_path):
                        logger.info(f"Checking for build system in {subdir_path}")
                        if build_system.detect(subdir_path):
                            return build_system.build(subdir_path, logger)

    logger.error(f"No supported build system found for {repo_path}")
    return False

def main() -> Tuple[List[str], List[str]]:
    successes = []
    fails = []
    print("\033[92m" + f"Current number successes: {len(successes)}\nCurrent number failures: {len(fails)}\nCurrent number total: {len(successes) + len(fails)}" + "\033[0m")

    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(LOGGER_DIR, repo_name)
        repo_path = os.path.join(REPOS_DIR, repo_name)
        logger.info(f"Analyzing {repo_path}")

        repo_build_exit_code = build_repo(repo_path, logger)

        if repo_build_exit_code == "success":
            logger.info(f"Success: Build succeeded for {repo_name}")
            successes.append(repo_name)
        else:
            logger.error(f"Error: Build failed for {repo_name}\nBuild failed for reason: {repo_build_exit_code}")
            print("\033[91m" + f"Error: Build failed for {repo_name}\nBuild failed for reason: {repo_build_exit_code}" + "\033[0m")
            fails.append(repo_name)

        print("\033[92m" + f"Current number successes: {len(successes)}\nCurrent number failures: {len(fails)}\nCurrent number total: {len(successes) + len(fails)}" + "\033[0m")

    return successes, fails

def check_java_installed():
    try:
        result = subprocess.run(['java', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print("Java is installed.")
        else:
            print("Java is not installed.")
    except FileNotFoundError:
        print("Java is not installed.")

if __name__ == "__main__":
    check_java_installed()
    successes, fails = main()

    print("Successes:", successes)
    print("Fails:", fails)
    print("Total number of repos:", len(successes) + len(fails))
    print("Number of successes:", len(successes))
    print("Number of fails:", len(fails))
