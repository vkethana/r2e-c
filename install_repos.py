from abc import ABC, abstractmethod
import os
import openai  
from openai import OpenAI
import subprocess  
from typing import List, Tuple
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger

# Initialize GPT-4 API
client = OpenAI(
    api_key="your key here"
)


class BuildSystem(ABC):
    @abstractmethod
    def detect(self, repo_path: str) -> bool:
        pass

    @abstractmethod
    def build(self, repo_path: str, logger) -> bool:
        pass

    def analyze_with_gpt(self, output: str) -> Tuple[str, str]:
        """Analyze command output with GPT-4 and return the suggested command and explanation."""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for debugging build issues on a Linux system."},
                    {"role": "user", "content": f"Here is a build error log:\n\n{output}\n\nCan you suggest a command to resolve this issue. Format your response precisely and succinctly like this: Suggested Command: ..."}
                ]
            )
            content = response.choices[0].message.content.strip()
            suggested_command = content.split("Suggested Command:", 1)[-1].strip().split('\n')[0]
            return suggested_command, content
        except Exception as e:
            return "", f"Error communicating with GPT-4: {str(e)}"

    def run_command(self, command: str, repo_path: str, logger) -> bool:
        """Run a command in the shell, capture its output, analyze it with GPT if it fails, and retry with GPT-suggested command."""
        logger.info(f"Running command: {command}")
        process = subprocess.run(command, shell=True, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.stdout.decode() + process.stderr.decode()
        logger.info(f"RETURN CODE IS: {process.returncode}")
        success = process.returncode == 0
        if not success:
            logger.error(f"Command failed: {command}\nOutput: {output}")
            suggested_command, gpt_analysis = self.analyze_with_gpt(output)
            logger.error(f"GPT-4 analysis: {gpt_analysis}")
            if suggested_command:
                logger.info(f"Running suggested command: {suggested_command}")
                subprocess.run(suggested_command, shell=True, cwd=repo_path)
                # Then try again
                subprocess.run(command, shell=True, cwd=repo_path)
            return False
        return True

class MakefileBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

    def build(self, repo_path: str, logger) -> bool:
        if not self.run_command('./autogen', repo_path, logger):
            logger.warning("./autogen failed, trying to run configure anyway")

        if not self.run_command('./configure', repo_path, logger):
            logger.warning("./configure failed, trying to run make anyway")

        return self.run_command('make', repo_path, logger)

class AutotoolsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger) -> bool:
        if not self.run_command('autoreconf -i', repo_path, logger):
            logger.warning("autoreconf -i failed")

        if not self.run_command('./autogen.sh', repo_path, logger):
            logger.warning("./autogen.sh failed")

        if not self.run_command('./configure', repo_path, logger):
            logger.warning("./configure failed")

        return self.run_command('make', repo_path, logger)

class CMakeBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'CMakeLists.txt'))

    def build(self, repo_path: str, logger) -> bool:
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        if not self.run_command('cmake ..', build_dir, logger):
            return False

        return self.run_command('cmake --build .', build_dir, logger)

class GradleBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'gradlew'))

    def build(self, repo_path: str, logger) -> bool:
        return self.run_command('./gradlew build', repo_path, logger)

def build_repo(repo_path: str, logger) -> bool:
    build_systems = [
        AutotoolsBuildSystem(),
        MakefileBuildSystem(),
        CMakeBuildSystem(),
        GradleBuildSystem(),
        # Add more build systems here
    ]

    for build_system in build_systems:
        if build_system.detect(repo_path):
            return build_system.build(repo_path, logger)

    logger.error(f"No supported build system found for {repo_path}")
    return False

def main() -> Tuple[List[str], List[str]]:
    successes = []
    fails = []

    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(os.path.join(LOGGER_DIR, repo_name), repo_name)
        repo_path = os.path.join(REPOS_DIR, repo_name)
        logger.info(f"Analyzing {repo_path}")

        if build_repo(repo_path, logger):
            logger.info(f"Success: Build succeeded for {repo_name}")
            successes.append(repo_name)
        else:
            logger.error(f"Error: Build failed for {repo_name}")
            fails.append(repo_name)

    return successes, fails

if __name__ == "__main__":
    successes, fails = main()

    print("Successes:", successes)
    print("Fails:", fails)
    print("Total number of repos:", len(successes) + len(fails))
    print("Number of successes:", len(successes))
    print("Number of fails:", len(fails))
