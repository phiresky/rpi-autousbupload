#!/usr/bin/env python3
"""
main loop starter for the ftpusbwatch program
"""
import os,sys,subprocess,time
os.chdir(os.path.dirname(__file__)) # ensure correct working direcory
try:
    import util,usbwait
    util.ntpTimeWait()


    config=util.loadConfig("config.json")
    log=util.initLogger(config)
except KeyboardInterrupt:
    raise
except Exception as e:
    """ if all else fails, do a git pull, hoping that will fix it """
    import traceback
    traceback.print_exc()
    util.waitForNetwork()
    gitlog = subprocess.check_output("git pull -f",shell=True).decode('utf-8').strip()
    subprocess.call("sync")
    print(gitlog)
    if gitlog == "Already up-to-date.":
        print("Could not start. Waiting and git-pulling")
        time.sleep(3600)
    subprocess.Popen("./main.py",shell=True)
    sys.exit(0)

try:
    log.info("boot|Waiting for network and updating")
    util.waitForNetwork()
    log.info("identification|"+str(util.getMac())+"|"+util.getIdentification())
    try:
        gitlog = subprocess.check_output("git pull",shell=True)
        subprocess.call("sync")
    except subprocess.CalledProcessError as e:
        log.warn("Update-Fehler|"+str(e.returncode)+":"+e.output.decode('utf-8'))
        log.exception("Git sync error")
    gitlog = gitlog.decode('utf-8').strip()
    log.info("git|"+str(util.getVersion())+'|'+gitlog)
    if gitlog == "Already up-to-date.":
        ignoreAlreadyMounted = len(sys.argv)>1 and sys.argv[1] == "skip"
        usbwait.USBWait(config).main_loop(not ignoreAlreadyMounted)
    else:
        # rerun this and exit
        subprocess.Popen("./main.py",shell=True)
except KeyboardInterrupt:
    log.info("|Killed by Keyboard")
except:
    log.exception("Error in main loop|")
