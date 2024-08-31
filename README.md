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
