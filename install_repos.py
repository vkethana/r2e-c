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
    def build(self, repo_path: str, logger) -> bool:
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

class MakefileBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running autogen")
        self.run_command('./autogen', repo_path, logger)
        
        logger.info("Running ./configure")
        self.run_command('./configure', repo_path, logger)
        
        logger.info("Running make")
        return self.run_command('make', repo_path, logger)

class AutotoolsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running autoreconf")
        if not self.run_command('autoreconf -i', repo_path, logger):
            return False
        logger.info("Running autogen.sh")
        self.run_command('./autogen.sh', repo_path, logger)
        logger.info("Running configure")
        if not self.run_command('./configure', repo_path, logger):
            return False
        logger.info("Running make")
        return self.run_command('make', repo_path, logger)


class CMakeBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'CMakeLists.txt'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running CMake")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        if os.system(f'cd {build_dir} && cmake .. && cmake --build .') != 0:
            return False
        return True

class GradleBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'gradlew'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running Gradle build")
        return self.run_command(f'cd {repo_path} && ./gradlew build', repo_path, logger)

class SConsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'SConstruct'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running SCons build")
        return self.run_command('scons', repo_path, logger)


class BazelBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'WORKSPACE'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running Bazel build")
        return self.run_command('bazel build //...', repo_path, logger)


class MesonBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'meson.build'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running Meson build")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        if not self.run_command(f'meson ..', build_dir, logger):
            return False
        
        return self.run_command('ninja', build_dir, logger)

class CustomScriptBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.sh'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running custom build.sh script")
        build_script = os.path.join(repo_path, 'build.sh')
        os.chmod(build_script, 0o755)  # Ensure the script is executable
        return self.run_command('./build.sh', repo_path, logger)


def build_repo(repo_path: str, logger) -> bool:
    build_systems = [
        AutotoolsBuildSystem(),
        MakefileBuildSystem(),
        CMakeBuildSystem(),
        GradleBuildSystem(),
        SConsBuildSystem(),
        BazelBuildSystem(),
        MesonBuildSystem(),
        CustomScriptBuildSystem(),  # Add the new build system
    ]

    for build_system in build_systems:
        if build_system.detect(repo_path):
            #return build_system
            return build_system.build(repo_path, logger)

    logger.error(f"No supported build system found for {repo_path}")
    return False

def main() -> Tuple[List[str], List[str]]:
    successes = []
    fails = []

    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(LOGGER_DIR, repo_name)
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
