from abc import ABC, abstractmethod
import os
from typing import List, Tuple
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger

class BuildSystem(ABC):
    @abstractmethod
    def detect(self, repo_path: str) -> bool:
        pass

    @abstractmethod
    def build(self, repo_path: str, logger) -> bool:
        pass

class MakefileBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running autogen")
        if os.system(f'cd {repo_path} && ./autogen') != 0:
            # Its ok if autogen fails, we can try to run configure anyway
            logger.warning("./autogen failed, trying to run configure anyway")

        logger.info("Running ./configure")
        if os.system(f'cd {repo_path} && ./configure') != 0:
            # Its ok if configure fails, we can try to run make anyway
            logger.warning("./configure failed, trying to run make anyway")

        logger.info("Running make")
        return os.system(f'cd {repo_path} && make') == 0

class AutotoolsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running autoreconf")
        if os.system(f'cd {repo_path} && autoreconf -i') != 0:
            return False
        logger.info("Running autogen.sh")
        os.system(f'cd {repo_path} && ./autogen.sh')
        logger.info("Running configure")
        if os.system(f'cd {repo_path} && ./configure') != 0:
            return False
        logger.info("Running make")
        return os.system(f'cd {repo_path} && make') == 0

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
        return os.system(f'cd {repo_path} && ./gradlew build') == 0


class SConsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'SConstruct'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running SCons build")
        return os.system(f'cd {repo_path} && scons') == 0

class BazelBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'WORKSPACE'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running Bazel build")
        return os.system(f'cd {repo_path} && bazel build //...') == 0

class MesonBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'meson.build'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running Meson build")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        if os.system(f'cd {build_dir} && meson .. && ninja') != 0:
            return False
        return True

class CustomScriptBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.sh'))

    def build(self, repo_path: str, logger) -> bool:
        logger.info("Running custom build.sh script")
        build_script = os.path.join(repo_path, 'build.sh')
        os.chmod(build_script, 0o755)  # Ensure the script is executable
        return os.system(f'cd {repo_path} && ./build.sh') == 0

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
