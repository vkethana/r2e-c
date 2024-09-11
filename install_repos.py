from abc import ABC, abstractmethod
import os
from typing import List, Tuple, Dict
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger
import subprocess
import re

class BuildSystem(ABC):
    @abstractmethod 
    def detect(self, repo_path: str) -> bool:
        pass

    @abstractmethod
    def build(self, repo_path: str, logger) -> Tuple[str, List[str], str]:
        pass

    def run_command(self, command: str, repo_path: str, logger) -> Tuple[bool, str]:
        log_file = os.path.join(LOGGER_DIR, f"{os.path.basename(repo_path)}_build.log")
        logger.info(f"Running command: {command}")
        logger.info(f"Logging output to: {log_file}")
        
        output = ""
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
                output += line
                log.write(line)
                logger.debug(line.strip())
            
            return_code = process.wait()
            log.write(f"Command finished with return code: {return_code}\n\n")
            
        return return_code == 0, output

class MakefileBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

    def build(self, repo_path: str, logger) -> Tuple[str, List[str], str]:
        logger.info("Running make")
        self.run_command('make clean', repo_path, logger)
        self.run_command('make distclean', repo_path, logger)
        self.run_command('rm -rf autom4te.cache', repo_path, logger)
        self.run_command('rm -f config.status config.cache config.log', repo_path, logger)

        logger.info("Running autogen")
        self.run_command('./autogen', repo_path, logger)
        
        logger.info("Running ./configure")
        success, output = self.run_command('./configure', repo_path, logger)
        if not success:
            return "configure failed", self.find_missing_headers(output), output
        
        logger.info("Running make")
        success, output = self.run_command('make', repo_path, logger)
        if not success:
            return "make failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

class AutotoolsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger) -> Tuple[str, List[str], str]:
        logger.info("Running autoreconf")
        success, output = self.run_command('autoreconf -i', repo_path, logger)
        if not success:
            return "autoreconf failed", self.find_missing_headers(output), output

        logger.info("Running autogen.sh")
        self.run_command('./autogen.sh', repo_path, logger)

        logger.info("Running configure")
        success, output = self.run_command('./configure', repo_path, logger)
        if not success:
            return "configure failed", self.find_missing_headers(output), output

        logger.info("Running make")
        success, output = self.run_command('make', repo_path, logger)
        if not success:
            return "make failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

class CMakeBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'CMakeLists.txt'))

    def build(self, repo_path: str, logger) -> Tuple[str, List[str], str]:
        # Clear Existing files
        self.run_command('rm -rf build/', repo_path, logger)
        self.run_command('rm -rf CMakeCache.txt', repo_path, logger)
        self.run_command('rm -rf CMakeFiles/', repo_path, logger)

        logger.info("Running CMake")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)

        success, output = self.run_command(f"cmake ..", build_dir, logger)
        if not success:
            return "cmake failed", self.find_missing_headers(output), output

        success, output = self.run_command(f"cmake --build .", build_dir, logger)
        if not success:
            return "cmake build failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

class SConsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'SConstruct'))

    def build(self, repo_path: str, logger):
        logger.info("Running SCons build")
        success, output = self.run_command(f"scons", build_dir, logger)
        if not success:
            return "scons failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

class BazelBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'WORKSPACE'))

    def build(self, repo_path: str, logger):
        self.run_command('bazel clean --expunge', repo_path, logger)

        logger.info("Running Bazel build")
        success, output = self.run_command(f"bazel build //...", build_dir, logger)

        if not success:
            return "bazel build failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))


class MesonBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'meson.build'))

    def build(self, repo_path: str, logger):
        self.run_command('rm -rf build/', repo_path, logger)

        logger.info("Running Meson build")
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)

        if not self.run_command(f'meson ..', build_dir, logger):
            return "meson failed", self.find_missing_headers(output), output

        if not self.run_command('ninja', build_dir, logger):
            return "ninja failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

class CustomScriptBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.sh'))

    def build(self, repo_path: str, logger):
        logger.info("Running custom build.sh script")
        build_script = os.path.join(repo_path, 'build.sh')
        os.chmod(build_script, 0o755)  # Ensure the script is executable
        if not self.run_command('./build.sh', repo_path, logger):
            return "build.sh failed", self.find_missing_headers(output), output

        return "success", [], ""

    def find_missing_headers(self, output: str) -> List[str]:
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        return list(set(missing_headers))

def build_repo(repo_path: str, logger) -> Tuple[str, str, List[str], str]:
    build_systems = [
        AutotoolsBuildSystem(),
        MakefileBuildSystem(),
        CMakeBuildSystem(),
        GradleBuildSystem(),
        SConsBuildSystem(),
        BazelBuildSystem(),
        MesonBuildSystem(),
        CustomScriptBuildSystem(),
    ]

    repo_name = os.path.basename(os.path.normpath(repo_path))
    possible_subdirs = [
        "src",
        "Source",
        os.path.join(repo_name, "src")
    ]

    for build_system in build_systems:
        if build_system.detect(repo_path):
            print(f"Build system detected: {build_system.__class__.__name__}")
            result, missing_headers, output = build_system.build(repo_path, logger)
            return build_system.__class__.__name__, result, missing_headers, output
        else:
            for subdir in possible_subdirs:
                subdir_path = os.path.join(repo_path, subdir)
                if os.path.exists(subdir_path):
                    logger.info(f"Checking for build system in {subdir_path}")
                    if build_system.detect(subdir_path):
                        print(f"Build system detected: {build_system.__class__.__name__}")
                        result, missing_headers, output = build_system.build(subdir_path, logger)
                        return build_system.__class__.__name__, result, missing_headers, output

    logger.error(f"No supported build system found for {repo_path}")
    return "Unknown", "no build system", [], ""

def main() -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], List[str]]:
    successes = {}
    failures = {}
    build_system_counts = {}
    all_missing_headers = []

    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(LOGGER_DIR, repo_name)
        repo_path = os.path.join(REPOS_DIR, repo_name)
        logger.info(f"Analyzing {repo_path}")

        build_system, result, missing_headers, output = build_repo(repo_path, logger)

        build_system_counts[build_system] = build_system_counts.get(build_system, 0) + 1

        if result == "success":
            logger.info(f"Success: Build succeeded for {repo_name}")
            successes[build_system] = successes.get(build_system, 0) + 1
        else:
            logger.error(f"Error: Build failed for {repo_name}\nBuild failed for reason: {result}")
            print(f"\033[91mError: Build failed for {repo_name}\nBuild failed for reason: {result}\033[0m")
            failures[build_system] = failures.get(build_system, 0) + 1

        all_missing_headers.extend(missing_headers)

        print_running_totals(successes, failures, build_system_counts, all_missing_headers)

    return successes, failures, build_system_counts, list(set(all_missing_headers))

def print_running_totals(successes: Dict[str, int], failures: Dict[str, int], build_system_counts: Dict[str, int], missing_headers: List[str]):
    total_successes = sum(successes.values())
    total_failures = sum(failures.values())
    total_repos = total_successes + total_failures

    print("\033[92m")
    print(f"Overall success rate: {total_successes}/{total_repos}")
    
    for build_system in build_system_counts:
        success_count = successes.get(build_system, 0)
        total_count = build_system_counts[build_system]
        print(f"Success rate for {build_system} Repos: {success_count}/{total_count}")

    print(f"Number of repos with no detectable buildsystem: {build_system_counts.get('Unknown', 0)}")
    print(f"Number of repos with package not found error: {len(missing_headers)}")
    print(f"Number of repos with ./configure errors: {failures.get('AutotoolsBuildSystem', 0)}")
    print(f"Number of repos with other errors: {total_failures - failures.get('AutotoolsBuildSystem', 0) - len(missing_headers)}")
    print("\033[0m")

if __name__ == "__main__":
    # Verify that scons is installed
    try:
        subprocess.run(['scons', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("SCons is not installed. Please install before running this script.")

    # Verify that bazel is installed, doesn't seem to be needed
    try:
        subprocess.run(['bazel', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("Bazel is not installed. Please install before running this script.")

    try:
        subprocess.run(['ninja', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("Ninja is not installed. Please install before running this script.")

    try:
        subprocess.run(['meson', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception("Meson is not installed. Please install before running this script.")


    successes, failures, build_system_counts, missing_headers = main()

    print("\nFinal Summary:")
    print_running_totals(successes, failures, build_system_counts, missing_headers)
    print("Missing headers:", missing_headers)
