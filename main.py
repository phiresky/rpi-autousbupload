#!/usr/bin/env python3
"""
main loop starter for the ftpusbwatch program
"""

import sys,util,usbwait,subprocess

config=util.loadConfig("config.json")
log=util.initLogger(config)
try:
    log.info("boot|Waiting for network and updating")
    util.waitForNetwork()
    gitlog = subprocess.check_output("GIT_SSH=./git_ssh.sh git pull",shell=True)
    gitlog = gitlog.decode('utf-8').strip()
    log.info("git|"+gitlog)
    if gitlog == "Already up-to-date.":
        ignoreAlreadyMounted = len(sys.argv)>1 and sys.argv[1] == "skip"
        usbwait.USBWait(config).main_loop(not ignoreAlreadyMounted)
    else:
        # rerun this and exit
        subprocess.Popen("python main.py",shell=True)
except KeyboardInterrupt:
    log.info("|Killed by Keyboard")
except:
    log.exception("Error in main loop")
