from abc import ABC, abstractmethod
import os
from typing import List, Tuple
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger
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

class MakefileBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

    def build(self, repo_path: str, logger):
        logger.info("Running make")
        self.run_command('make clean', repo_path, logger)
        self.run_command('make distclean', repo_path, logger)
        self.run_command('rm -rf autom4te.cache', repo_path, logger)
        self.run_command('rm -f config.status config.cache config.log', repo_path, logger)

        logger.info("Running autogen")
        self.run_command('./autogen', repo_path, logger)
        
        logger.info("Running ./configure")
        self.run_command('./configure', repo_path, logger)
        
        logger.info("Running make")
        if not self.run_command('make', repo_path, logger):
            return "make failed"

        return "success"

class AutotoolsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger):
        logger.info("Running autoreconf")
        if not self.run_command('autoreconf -i', repo_path, logger):
            return "autoreconf failed"
        logger.info("Running autogen.sh")
        self.run_command('./autogen.sh', repo_path, logger)
        logger.info("Running configure")
        if not self.run_command('./configure', repo_path, logger):
            return "configure failed"
        logger.info("Running make")
        if not self.run_command('make', repo_path, logger):
            return "make failed"

        return "success"


class CMakeBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'CMakeLists.txt'))


    def build(self, repo_path: str, logger):
        # Clear Existing files
        self.run_command('rm -rf build/', repo_path, logger)
        self.run_command('rm -rf CMakeCache.txt', repo_path, logger)
        self.run_command('rm -rf CMakeFiles/', repo_path, logger)

        logger.info("Running CMake")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)

        if not self.run_command(f"cmake ..", build_dir, logger):
            return "cmake failed"

        if not self.run_command(f"cmake --build .", build_dir, logger):
            return "cmake build failed"

        return "success"

class GradleBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'gradlew'))

    def build(self, repo_path: str, logger):
        self.run_command('./gradlew clean', repo_path, logger)
        self.run_command('rm -rf .gradle/', repo_path, logger)
        self.run_command('rm -rf build/', repo_path, logger)

        logger.info("Running Gradle build")
        if not self.run_command(f'./gradlew build', repo_path, logger):
            return "gradle failed"
        return "success"

class SConsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'SConstruct'))

    def build(self, repo_path: str, logger):
        logger.info("Running SCons build")
        if not self.run_command('scons', repo_path, logger):
            return "scons failed"

        return "success"


class BazelBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'WORKSPACE'))

    def build(self, repo_path: str, logger):
        self.run_command('bazel clean --expunge', repo_path, logger)

        logger.info("Running Bazel build")

        if not self.run_command('bazel build //...', repo_path, logger):
            return "bazel build failed"

        return "success"


class MesonBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'meson.build'))

    def build(self, repo_path: str, logger):
        self.run_command('rm -rf build/', repo_path, logger)

        logger.info("Running Meson build")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)

        if not self.run_command(f'meson ..', build_dir, logger):
            return "meson failed"

        if not self.run_command('ninja', build_dir, logger):
            return "ninja failed"

        return "success"

class CustomScriptBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.sh'))

    def build(self, repo_path: str, logger):
        logger.info("Running custom build.sh script")
        build_script = os.path.join(repo_path, 'build.sh')
        os.chmod(build_script, 0o755)  # Ensure the script is executable
        if not self.run_command('./build.sh', repo_path, logger):
            return "build.sh failed"

        return "success"


def build_repo(repo_path: str, logger):
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

if __name__ == "__main__":
    # Verify that scons is installed
    try:
        subprocess.run(['scons', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("SCons is not installed. Please install before running this script.")

    # Verify that bazel is installed, doesn't seem to be needed
    '''
    try:
        subprocess.run(['bazel', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("Bazel is not installed. Please install before running this script.")
    '''

    try:
        subprocess.run(['ninja', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("Ninja is not installed. Please install before running this script.")

    successes, fails = main()

    print("Successes:", successes)
    print("Fails:", fails)
    print("Total number of repos:", len(successes) + len(fails))
    print("Number of successes:", len(successes))
    print("Number of fails:", len(fails))
