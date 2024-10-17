# R2E-C
This repo is a work-in-progress attempt to expand R2E ([r2e.dev](r2e.dev)), a tool for turning Python GitHub repos into programming agent environments, to support the C programming language. There are several parts to this process:

0) Cloning the relevant repos which we want to generate tests for (using `clone_repos.py`).
1) **Buildsystem Detection**, which is handled by `install_repos.py`. This script reads an arbitrary GitHub repo and attempts to figure out what buildsystem, if any, it uses
2) **Test Extraction**, which is handled by `generate_self_equiv_tests.py`. This script attempts to grab relevant functions from the repos and extract them into a JSON. We are also working to add dependency slicing, which will identify what imports / headers / other functions are necessary for a given test to function
3) **Test Execution**, which is handled by `run_self_equiv_tests.py`. This runs the tests generated in the previous step.
   
# Usage
1. Edit `repos.json` with a list of repos you want to clone
2. Run `python clone_repos.py`
3. Repos will be cloned to the `repos/` directory
4. Now run `python install_repos.py`
5. Logging data will be outputted to `logs/` and total success and failure rates will be displayed like so:
   
```
Successes:
['wg___wrk', 'samyk___pwnat', 'ioquake___ioq3']
Fails:
['opsengine___cpulimit', 'gamelinux___passivedns', 'bakkeby___dwm-flexipatch', 'grbl___grbl', 'taviso___ctypes.sh', 'hashcat___hashcat-legacy', 'alibaba___LVS']
Total number of repos:
10
Number of successes:
3
Number of fails:
7
```
