import re
import json
import clang.cindex
from pathlib import Path
import subprocess
import tempfile
import difflib
import hashlib
from datetime import datetime
from paths import SELF_EQUIV_OUTPUT_DIR

'''
To run this script, makesure LLVM and Clang are installed on your system.
Specifically, make sure llvm-10 is installed
'''

llvm_library_path = '/usr/lib/llvm-10/lib/libclang.so.1'

class CFunctionExtractor:
    def __init__(self, num_tests=10):
        # Initialize clang with the new library path
        clang.cindex.Config.set_library_file(llvm_library_path)
        self.index = clang.cindex.Index.create()
        self.num_tests = num_tests
        self.extracted_count = 0
        
    def extract_function_with_context(self, filepath, cursor, tu):
        """Extract function and its dependencies"""
        with open(filepath) as f:
            content = f.read()
            
        # Get function source using line-based extraction
        start_line = cursor.extent.start.line - 1
        end_line = cursor.extent.end.line
        function_source = "\n".join(content.splitlines()[start_line:end_line])
        
        # Get required includes and typedefs by traversing the full translation unit
        includes = set()
        typedefs = set()
        
        def collect_dependencies(node):
            if node.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE:
                includes.add(node.displayname)
            elif node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
                typedefs.add(node.displayname)

        # Traverse the translation unit using get_children()
        for node in tu.cursor.get_children():
            collect_dependencies(node)
        
        return {
            'function_name': cursor.spelling,
            'source': function_source,
            'includes': list(includes),
            'typedefs': list(typedefs),
            'signature': self.get_function_signature(cursor),
            'file_path': str(filepath),
            'start_line': start_line + 1,
            'end_line': end_line
        }
    
    def get_function_signature(self, cursor):
        """Extract function signature including return type and parameters"""
        return_type = cursor.result_type.spelling
        params = [p.type.spelling for p in cursor.get_arguments()]
        return f"{return_type} {cursor.spelling}({', '.join(params)})"
    
    def is_testable_function(self, cursor):
        """Determine if a function is suitable for testing"""
        # Skip static functions
        if cursor.storage_class == clang.cindex.StorageClass.STATIC:
            return False
            
        # Skip functions with no parameters
        if len(list(cursor.get_arguments())) == 0:
            return False
            
        # Skip functions with complex return types (pointers, structs)
        return_type = cursor.result_type.spelling
        if '*' in return_type or 'struct' in return_type:
            return False
            
        return True
    
    def extract_from_repo(self, repo_path):
        """Extract testable functions from a repository"""
        testable_functions = []
        
        for c_file in Path(repo_path).rglob('*.c'):
            if self.extracted_count >= self.num_tests:
                break
                
            try:
                print(f"Processing {c_file}")
                # Parsing with optional include paths (add more paths if needed)
                tu = self.index.parse(str(c_file), args=['-I', '/usr/include', '-I', '/usr/local/include'])
                if not tu:
                    print(f"Failed to parse {c_file}")
                    continue

                # Walk through all nodes in the translation unit
                for cursor in tu.cursor.walk_preorder():
                    if self.extracted_count >= self.num_tests:
                        break
                        
                    if (cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL and 
                        self.is_testable_function(cursor)):
                        func_info = self.extract_function_with_context(str(c_file), cursor, tu)
                        testable_functions.append(func_info)
                        self.extracted_count += 1
                        print(f"Found testable function ({self.extracted_count}/{self.num_tests}): {func_info['function_name']}")
                        
            except Exception as e:
                print(f"Error processing {c_file}: {e}")
                
        return testable_functions

class SelfEquivalenceTester:
    def __init__(self):
        self.gcc_flags = ['-O0', '-Wall', '-Wextra']
        
    def generate_test_cases(self, function_info):
        """Generate test cases based on function signature"""
        return_type = function_info['signature'].split()[0]
        test_cases = []
        
        # Parse parameters from signature
        params_str = function_info['signature'].split('(')[1].split(')')[0]
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        
        # Generate a few test cases with different parameter values
        for i in range(3):  # Generate 3 test cases per function
            test_case = {
                'inputs': [],
                'expected_output': None
            }
            
            for param_type in params:
                # Generate appropriate test values based on type
                if 'int' in param_type:
                    test_case['inputs'].append(i * 10)  # Simple integer progression
                elif 'float' in param_type or 'double' in param_type:
                    test_case['inputs'].append(i * 10.5)
                else:
                    test_case['inputs'].append(0)  # Default for unknown types
                    
            test_cases.append(test_case)
            
        return test_cases
        
    def create_test_harness(self, function_info, test_cases):
        """Create a test harness for the function"""
        includes = '\n'.join(f'#include {inc}' for inc in function_info['includes'])
        typedefs = '\n'.join(function_info['typedefs'])
        
        test_code = []
        for i, test in enumerate(test_cases):
            params = ', '.join(str(p) for p in test['inputs'])
            test_code.append(f"""
    printf("Test case {i + 1}:\\n");
    result = {function_info['function_name']}({params});
    printf("Input: ({params}), Output: %d\\n", result);
""")
            
        return f"""
{includes}
{typedefs}
{function_info['source']}

// Test harness
int main() {{
    {function_info['signature'].split()[0]} result;
    
    {''.join(test_code)}
    return 0;
}}
"""

def save_to_json(functions, test_cases, output_dir=SELF_EQUIV_OUTPUT_DIR):
    """Save extracted functions and test cases to JSON files"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save functions
    functions_file = Path(output_dir) / f"functions_{timestamp}.json"
    with open(functions_file, 'w') as f:
        json.dump(functions, f, indent=2)
    print(f"Saved functions to {functions_file}")
    
    # Save test cases
    tests_file = Path(output_dir) / f"tests_{timestamp}.json"
    with open(tests_file, 'w') as f:
        json.dump(test_cases, f, indent=2)
    print(f"Saved test cases to {tests_file}")

def main():
    num_tests = 10
    extractor = CFunctionExtractor(num_tests=num_tests)
    tester = SelfEquivalenceTester()
    
    # Run the function extractor on the provided repo path
    repo_path = "repos/repos_10/git___git"
    functions = extractor.extract_from_repo(repo_path)
    
    # Generate test cases for each function
    all_test_cases = {}
    for func in functions:
        test_cases = tester.generate_test_cases(func)
        h = tester.create_test_harness(func, test_cases)

        all_test_cases[func['function_name']] = {
            'test_cases': test_cases,
            'harness': h
        }
    
    # Save results to JSON
    save_to_json(functions, all_test_cases)
    
    print(f"\nExtraction Summary:")
    print(f"Found {len(functions)} testable functions")
    for func in functions:
        print(f"\nFunction: {func['function_name']}")
        print(f"Signature: {func['signature']}")
        print(f"Source length: {len(func['source'])} bytes")
        print(f"File: {func['file_path']}:{func['start_line']}-{func['end_line']}")
        print(f"Number of test cases: {len(all_test_cases[func['function_name']]['test_cases'])}")

if __name__ == "__main__":
    main()
