'''
USAGE
python -m unittest test_build_systems.py -k test_curl_cmake_build
'''
import unittest
import os
from unittest.mock import Mock, patch
from typing import List, Dict
from install_repos import *

class BuildSystemTestCase:
    """Helper class to define expected test results for a repo"""
    def __init__(self, 
                 repo_path: str,
                 expected_system: str,
                 expected_result: str = "success",
                 expected_headers: List[str] = None,
                 expected_additional_systems: List[Dict[str, str]] = None):
        """
        Args:
            repo_path: Path to the test repository
            expected_system: Expected build system to be detected
            expected_result: Expected build result ("success" or error message)
            expected_headers: Expected missing headers to be found
            expected_additional_systems: Expected additional build systems that succeeded
        """
        self.repo_path = repo_path
        self.expected_system = expected_system
        self.expected_result = expected_result
        self.expected_headers = expected_headers or []
        self.expected_additional_systems = expected_additional_systems or []

class TestBuildSystems(unittest.TestCase):
    def setUp(self):
        # Create mock logger
        self.mock_logger = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.error = Mock()
        self.mock_logger.debug = Mock()

    def verify_build_result(self, test_case: BuildSystemTestCase, build_result: Dict[str, any]):
        """Helper method to verify build results against expected values"""
        '''
        self.assertEqual(build_result["build_system"], test_case.expected_system,
                        "Incorrect build system detected")
        '''
        
        self.assertEqual(build_result["result"], test_case.expected_result,
                        "Build result does not match expected")
        
        '''
        if test_case.expected_headers:
            self.assertEqual(set(build_result["missing_headers"]), 
                           set(test_case.expected_headers),
                           "Missing headers do not match expected")
            
        if test_case.expected_additional_systems:
            self.assertEqual(build_result["additional_buildsystems"],
                           test_case.expected_additional_systems,
                           "Additional build systems do not match expected")
        '''

    def test_curl_cmake_build(self):
        """Test building curl which uses CMake"""
        test_case = BuildSystemTestCase(
            repo_path="repos/repos_10/curl___curl",
            expected_system="CMakeBuildSystem",
            expected_result="success"
        )
        
        build_result = build_repo(test_case.repo_path, self.mock_logger)
        self.verify_build_result(test_case, build_result)

    def test_sqlite_make_build(self):
        """Test building sqlite which uses Make"""
        test_case = BuildSystemTestCase(
            repo_path="repos/repos_10/sqlite___sqlite",
            expected_system="MakefileBuildSystem",
            expected_result="success"
        )
        
        build_result = build_repo(test_case.repo_path, self.mock_logger)
        self.verify_build_result(test_case, build_result)

    def test_failed_build_with_alternatives(self):
        """Test a case where primary build system fails but alternatives succeed"""
        '''
        test_case = BuildSystemTestCase(
            repo_path="repos/repos_10/example___project",
            expected_system="CMakeBuildSystem",
            expected_result="cmake failed",
            expected_headers=["missing.h"],
            expected_additional_systems=[
                {"name": "MakefileBuildSystem", "result": "success"}
            ]
        )
        
        build_result = build_repo(test_case.repo_path, self.mock_logger)
        self.verify_build_result(test_case, build_result)
        '''

    def test_no_build_system(self):
        '''
        """Test handling of repos with no recognized build system"""
        test_case = BuildSystemTestCase(
            repo_path="repos/repos_10/no_build_system",
            expected_system="Unknown",
            expected_result="no build system"
        )
        
        build_result = build_repo(test_case.repo_path, self.mock_logger)
        self.verify_build_result(test_case, build_result)
        '''
        pass

if __name__ == '__main__':
    unittest.main()
