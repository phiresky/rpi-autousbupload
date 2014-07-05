#!/usr/bin/env python3
"""
main loop starter for the ftpusbwatch program
"""
try:
    import os,sys,util,usbwait,subprocess

    os.chdir(os.path.dirname(__file__)) # ensure correct working direcory

    config=util.loadConfig("config.json")
    log=util.initLogger(config)
except KeyboardInterrupt:
    raise
except:
    """ if all else fails, do a git pull, hoping that will fix it """
    util.waitForNetwork()
    gitlog = subprocess.check_output("git pull -f",shell=True)
    subprocess.call("sync")
    print(gitlog.decode('utf-8'))
    subprocess.Popen("./main.py",shell=True)
    sys.exit(0)

try:
    log.info("boot|Waiting for network and updating")
    util.waitForNetwork()
    try:
        gitlog = subprocess.check_output("git pull",shell=True)
        subprocess.call("sync")
    except subprocess.CalledProcessError as e:
        log.warn(str(e.returncode)+":"+e.output)
        log.exception()
    gitlog = gitlog.decode('utf-8').strip()
    log.info("git|"+gitlog)
    if gitlog == "Already up-to-date.":
        ignoreAlreadyMounted = len(sys.argv)>1 and sys.argv[1] == "skip"
        usbwait.USBWait(config).main_loop(not ignoreAlreadyMounted)
    else:
        # rerun this and exit
        subprocess.Popen("./main.py",shell=True)
except KeyboardInterrupt:
    log.info("|Killed by Keyboard")
except:
    log.exception("Error in main loop")
