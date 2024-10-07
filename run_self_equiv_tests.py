import json
import subprocess
import tempfile
from pathlib import Path
import difflib
import sys
import os
import logging
from datetime import datetime

class TestRunner:
    def __init__(self, functions_file, tests_file, output_dir="test_results"):
        self.gcc_flags = ['-O0', '-Wall', '-Wextra']
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        log_file = self.output_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Load test data
        with open(functions_file) as f:
            self.functions = json.load(f)
        with open(tests_file) as f:
            self.test_cases = json.load(f)
            
        logging.info(f"Loaded {len(self.functions)} functions and their test cases")

    def compile_and_run(self, source_code, function_name):
        """Compile and run a test harness"""
        with tempfile.NamedTemporaryFile(suffix='.c', mode='w', delete=False) as f:
            f.write(source_code)
            source_file = f.name
            
        executable = source_file + '.exe'
        
        try:
            # Compile
            compile_cmd = ['gcc'] + self.gcc_flags + [source_file, '-o', executable]
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True
            )
            
            if compile_result.returncode != 0:
                logging.error(f"Compilation failed for {function_name}:")
                logging.error(compile_result.stderr)
                return None
                
            # Run
            run_result = subprocess.run(
                [executable],
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            return run_result.stdout
            
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout running tests for {function_name}")
            return None
        except Exception as e:
            logging.error(f"Error running tests for {function_name}: {e}")
            return None
        finally:
            # Cleanup
            if os.path.exists(source_file):
                os.unlink(source_file)
            if os.path.exists(executable):
                os.unlink(executable)

    def run_equivalence_test(self, original_func, generated_func):
        """Run equivalence test between original and generated function"""
        test_info = self.test_cases[original_func['function_name']]
        
        # Run original function tests
        original_output = self.compile_and_run(
            test_info['harness'],
            original_func['function_name']
        )
        
        if original_output is None:
            return False, "Original function failed to compile/run"
            
        # Create harness for generated function by replacing the function implementation
        generated_harness = test_info['harness'].replace(
            original_func['source'],
            generated_func['source']
        )
        
        # Run generated function tests
        generated_output = self.compile_and_run(
            generated_harness,
            generated_func['function_name']
        )
        
        if generated_output is None:
            return False, "Generated function failed to compile/run"
            
        # Compare outputs
        if original_output == generated_output:
            return True, "Outputs match exactly"
            
        # Generate detailed diff if outputs don't match
        diff = list(difflib.unified_diff(
            original_output.splitlines(),
            generated_output.splitlines(),
            fromfile='Original',
            tofile='Generated'
        ))
        
        return False, f"Outputs differ:\n{''.join(diff)}"

    def save_results(self, results):
        """Save test results to JSON"""
        output_file = self.output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results saved to {output_file}")

    def run_all_tests(self, generated_functions):
        """Run all equivalence tests"""
        results = []
        
        for orig_func in self.functions:
            func_name = orig_func['function_name']
            logging.info(f"Testing function: {func_name}")
            
            # Find corresponding generated function
            gen_func = next(
                (f for f in generated_functions if f['function_name'] == func_name),
                None
            )
            
            if gen_func is None:
                logging.warning(f"No generated function found for {func_name}")
                results.append({
                    'function_name': func_name,
                    'status': 'skipped',
                    'reason': 'No generated function found'
                })
                continue
                
            # Run equivalence test
            is_equivalent, details = self.run_equivalence_test(orig_func, gen_func)
            
            results.append({
                'function_name': func_name,
                'status': 'equivalent' if is_equivalent else 'different',
                'details': details,
                'original_source': orig_func['source'],
                'generated_source': gen_func['source']
            })
            
            logging.info(f"Function {func_name}: {'PASS' if is_equivalent else 'FAIL'}")
            
        return results

def main():
    if len(sys.argv) != 4:
        print("Usage: python test_runner.py <functions_file> <tests_file> <generated_functions_file>")
        sys.exit(1)
        
    functions_file = sys.argv[1]
    tests_file = sys.argv[2]
    generated_functions_file = sys.argv[3]
    
    # Load generated functions
    with open(generated_functions_file) as f:
        generated_functions = json.load(f)
    
    # Create and run tests
    runner = TestRunner(functions_file, tests_file)
    results = runner.run_all_tests(generated_functions)
    
    # Save results
    runner.save_results(results)
    
    # Print summary
    total = len(results)
    equivalent = sum(1 for r in results if r['status'] == 'equivalent')
    print(f"\nTest Summary:")
    print(f"Total functions tested: {total}")
    print(f"Equivalent implementations: {equivalent}")
    print(f"Success rate: {(equivalent/total)*100:.2f}%")

if __name__ == "__main__":
    main()
