from abc import ABC, abstractmethod
import os
from typing import List, Dict, Tuple
from paths import REPOS_DIR, LOGGER_DIR
from utils import setup_logger
import subprocess
import re
from openai import OpenAI 
from collections import defaultdict

class BuildSystem(ABC):
    @abstractmethod 
    def detect(self, repo_path: str) -> bool:
        pass

    def find_missing_headers(self, output: str) -> List[str]:
        """Base implementation for finding missing headers"""
        missing_headers = re.findall(r'fatal error: (.+?): No such file or directory', output)
        missing_headers.extend(re.findall(r'#include <(.+?)>', output))
        return list(set(missing_headers))

    def run_command(self, command: str, repo_path: str, logger) -> Dict[str, str]:
        """Base implementation for running commands"""
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
            
        return {
            "success": return_code == 0,
            "output": output
        }

    @abstractmethod
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        pass

class MakeBasedSystem(BuildSystem):
    """Base class for make-based build systems"""
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }

        # Common cleanup steps
        self.run_command('make clean', repo_path, logger)
        self.run_command('make distclean', repo_path, logger)
        self.run_command('rm -rf autom4te.cache', repo_path, logger)
        self.run_command('rm -f config.status config.cache config.log', repo_path, logger)

        # Run configure if it exists
        if os.path.exists(os.path.join(repo_path, 'configure')):
            cmd_result = self.run_command('./configure', repo_path, logger)
            res["output"] += cmd_result["output"]

        # Run make
        cmd_result = self.run_command('make', repo_path, logger)
        res["output"] += cmd_result["output"]
        
        if not cmd_result["success"]:
            res["result"] = "make failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])

        return res

class MakefileBuildSystem(MakeBasedSystem):
    def detect(self, repo_path: str) -> bool:
        makefile_variants = ['Makefile', 'makefile', 'MAKEFILE']
        return any(os.path.isfile(os.path.join(repo_path, variant)) for variant in makefile_variants)

class AutotoolsBuildSystem(MakeBasedSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'configure.ac'))

    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }

        # Run autoreconf
        cmd_result = self.run_command('autoreconf -i', repo_path, logger)
        res["output"] += cmd_result["output"]
        if not cmd_result["success"]:
            res["result"] = "autoreconf failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            return res

        # Run parent class build method (handles configure and make)
        parent_res = super().build(repo_path, logger)
        res["output"] += parent_res["output"]
        
        if parent_res["result"] != "success":
            res.update(parent_res)

        return res


class CMakeBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'CMakeLists.txt'))
        
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Create build directory
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        # Run CMake
        cmd_result = self.run_command('cmake ..', build_dir, logger)
        res["output"] += cmd_result["output"]
        if not cmd_result["success"]:
            res["result"] = "cmake failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            return res
            
        # Run make
        cmd_result = self.run_command('make', build_dir, logger)
        res["output"] += cmd_result["output"]
        if not cmd_result["success"]:
            res["result"] = "make failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

class SConsBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'SConstruct')) or \
               os.path.isfile(os.path.join(repo_path, 'Sconstruct'))
               
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Clean first
        self.run_command('scons -c', repo_path, logger)
        
        # Run SCons build
        cmd_result = self.run_command('scons', repo_path, logger)
        res["output"] += cmd_result["output"]
        
        if not cmd_result["success"]:
            res["result"] = "scons failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

class BazelBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'WORKSPACE')) or \
               os.path.isfile(os.path.join(repo_path, 'WORKSPACE.bazel'))
               
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Clean first
        self.run_command('bazel clean', repo_path, logger)
        
        # Run Bazel build
        cmd_result = self.run_command('bazel build //...', repo_path, logger)
        res["output"] += cmd_result["output"]
        
        if not cmd_result["success"]:
            res["result"] = "bazel failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

class MesonBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'meson.build'))
        
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        build_dir = os.path.join(repo_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        # Setup build directory
        cmd_result = self.run_command('meson setup ..', build_dir, logger)
        res["output"] += cmd_result["output"]
        if not cmd_result["success"]:
            res["result"] = "meson setup failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            return res
            
        # Run build
        cmd_result = self.run_command('ninja', build_dir, logger)
        res["output"] += cmd_result["output"]
        if not cmd_result["success"]:
            res["result"] = "ninja failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

class CustomScriptBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        build_scripts = ['build.sh', 'compile.sh', 'make.sh', 'build']
        return any(os.path.isfile(os.path.join(repo_path, script)) for script in build_scripts)
        
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Try different build scripts in order of preference
        build_scripts = ['build.sh', 'compile.sh', 'make.sh', 'build']
        for script in build_scripts:
            script_path = os.path.join(repo_path, script)
            if os.path.isfile(script_path):
                # Make script executable
                os.chmod(script_path, 0o755)
                cmd_result = self.run_command(f'./{script}', repo_path, logger)
                res["output"] += cmd_result["output"]
                
                if not cmd_result["success"]:
                    res["result"] = f"build script {script} failed"
                    res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
                return res
                
        return res

class SlnBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return any(f.endswith('.sln') for f in os.listdir(repo_path))
        
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Find .sln file
        sln_files = [f for f in os.listdir(repo_path) if f.endswith('.sln')]
        if not sln_files:
            res["result"] = "no .sln file found"
            return res
            
        sln_file = sln_files[0]
        
        # Build using MSBuild
        cmd_result = self.run_command(f'msbuild {sln_file}', repo_path, logger)
        res["output"] += cmd_result["output"]
        
        if not cmd_result["success"]:
            res["result"] = "msbuild failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

class GradleBuildSystem(BuildSystem):
    def detect(self, repo_path: str) -> bool:
        return os.path.isfile(os.path.join(repo_path, 'build.gradle'))
        
    def build(self, repo_path: str, logger) -> Dict[str, any]:
        res = {
            "result": "success",
            "missing_headers": [],
            "output": "",
        }
        
        # Clean first
        self.run_command('./gradlew clean', repo_path, logger)
        
        # Run Gradle build
        cmd_result = self.run_command('./gradlew build', repo_path, logger)
        res["output"] += cmd_result["output"]
        
        if not cmd_result["success"]:
            res["result"] = "gradle build failed"
            res["missing_headers"] = self.find_missing_headers(cmd_result["output"])
            
        return res

def build_repo(repo_path: str, logger) -> Dict[str, any]:
    build_systems = [
        CustomScriptBuildSystem(),
        SConsBuildSystem(),
        AutotoolsBuildSystem(),
        CMakeBuildSystem(),
        SlnBuildSystem(),
        MakefileBuildSystem(),
        GradleBuildSystem(),
        BazelBuildSystem(),
        MesonBuildSystem(),
    ]

    res = {
        "build_system": "Unknown",
        "result": "no build system",
        "missing_headers": [],
        "output": "",
        "additional_buildsystems": []
    }

    # Try automatic detection first
    for build_system in build_systems:
        if build_system.detect(repo_path):
            print(f"Build system detected: {build_system.__class__.__name__}")
            build_res = build_system.build(repo_path, logger)
            
            res["build_system"] = build_system.__class__.__name__
            res.update(build_res)
            
            # If build failed, try other build systems
            if build_res["result"] != "success":
                print("Primary build system failed, trying alternatives...")
                for alt_system in build_systems:
                    if alt_system.__class__.__name__ != res["build_system"]:
                        if alt_system.detect(repo_path):
                            alt_res = alt_system.build(repo_path, logger)
                            if alt_res["result"] == "success":
                                res["additional_buildsystems"].append({
                                    "name": alt_system.__class__.__name__,
                                    "result": "success"
                                })
                            
            return res

    logger.error(f"No supported build system found for {repo_path}")
    return res

def main() -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]], List[str]]:
    successes = defaultdict(list)
    failures = defaultdict(list)
    build_system_counts = defaultdict(list)
    all_missing_headers = []
    buildsystem_categories = defaultdict(list)
    print("Running installer on ", REPOS_DIR)
    print("There are ", len(os.listdir(REPOS_DIR)), " repos to be installed")

    for repo_name in os.listdir(REPOS_DIR):
        logger = setup_logger(LOGGER_DIR, repo_name)
        repo_path = os.path.join(REPOS_DIR, repo_name)
        logger.info(f"Analyzing {repo_path}")

        build_res = build_repo(repo_path, logger)

        build_system = build_res["build_system"]
        build_system_counts[build_system].append(repo_name)

        if build_res["result"] == "success":
            logger.info(f"Success: Build succeeded for {repo_name}")
            successes[build_system].append(repo_name)
        else:
            logger.error(f"Error: Build failed for {repo_name}\nBuild failed for reason: {build_res['result']}")
            print(f"\033[91mError: Build failed for {repo_name}\nBuild failed for reason: {build_res['result']}\033[0m")
            failures[build_system].append(repo_name)

            if build_res["additional_buildsystems"]:
                logger.info(f"Alternative build systems succeeded: {build_res['additional_buildsystems']}")

        all_missing_headers.extend(build_res["missing_headers"])
        print_running_totals(successes, failures, build_system_counts, all_missing_headers)

    return successes, failures, build_system_counts, list(set(all_missing_headers))

def print_running_totals(successes: Dict[str, int], failures: Dict[str, int], build_system_counts: Dict[str, int], missing_headers: List[str]):
    total_successes = len(successes.values())
    total_failures = len(failures.values())
    total_repos = total_successes + total_failures

    print("\033[92m")
    print(f"Overall success rate: {total_successes}/{total_repos}")
    
    for build_system in build_system_counts:
        success_count = len(successes.get(build_system, 0))
        total_count = len(build_system_counts[build_system])
        print(f"Success rate for {build_system} Repos: {success_count}/{total_count}")

    print(f"Number of repos with no detectable buildsystem: {build_system_counts.get('Unknown', 0)}")
    print(f"Number of repos with package not found error: {len(missing_headers)}")
    print("\033[0m")

def check_dependency(command: str, name: str):
    try:
        subprocess.run([command, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Exception(f"{name} is not installed. Please install before running this script.")


if __name__ == "__main__":
    check_dependency('scons', 'SCons')
    check_dependency('bazel', 'Bazel')
    check_dependency('ninja', 'Ninja')
    check_dependency('meson', 'Meson')
    successes, failures, build_system_counts, missing_headers = main()

    print("\nFinal Summary:")
    print_running_totals(successes, failures, build_system_counts, missing_headers)
    print("Missing headers:", missing_headers)

