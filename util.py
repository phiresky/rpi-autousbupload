"""
utility functions for usbftpwatch
"""

import json
import datetime
import urllib,urllib.request
import time
import os,os.path
import smtplib
import socket
from email.mime.text import MIMEText
from email.header import Header
def getMountPoint(devid):
    """ find out the mount point given a device path """
    for mount in open('/proc/mounts'):
        dev, mountpoint, fstype = mount.split()[:3]
        if dev == devid:
            return mountpoint
    return None
    # if fstype in ('fuseblk','vfat') and dev.startswith('/dev/sd'):
    #    print(mountpoint)

def getPartitions():
    """ gets a list of sd?? partitions like sda1,sda2,sdb1,sdc1"""
    devlist=open("/proc/partitions").read().strip().split("\n")[2:]
    devlist=map(lambda x:x.split()[-1],devlist)
    return [dev for dev in devlist if len(dev)==4 and dev[0:2]=="sd"]

def loadConfig(fname):
    """ load a json config file, use *.sample if it does not exist """
    if not os.path.isfile(fname):
        import shutil
        shutil.copy(fname+".sample",fname)
    with open(fname,encoding='utf-8') as jsonfile:
        try:
            config = json.load(jsonfile)
        except:
            print("FATAL ERROR: errors in config file")
            raise
    formatdict(config,config)
    return config

def relpathjoin(a,b):
    """ join(/mountpoint, /DCIM) returns /mountpoint/DCIM in contrast to os.path.join"""
    return os.path.join(a,b.lstrip("/"))

def getVersion():
    from subprocess import check_output as run
    return int(run("git rev-list HEAD --count",shell=True).decode('utf-8'))

def initLogger(config):
    """ create a file and mail logger """
    import logging
    import logging.handlers
    loggername = config['devicename']
    logger = logging.getLogger(loggername)
    if not os.path.exists("log"):
        os.mkdir("log")
    filelog = logging.handlers.RotatingFileHandler(
            "log/"+loggername+".log",
            maxBytes=1024*1024,
            backupCount=20)
    console = logging.StreamHandler()
    maillog = logging.StreamHandler(stream=MailStream(config))
    phplog = logging.StreamHandler(stream=PHPUploadStream(config))
    formatter = logging.Formatter(
        '%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    filelog.setFormatter(formatter)
    console.setFormatter(formatter)
    maillog.setFormatter(formatter)
    phplog.setFormatter(formatter)
    phplog.terminator="|END|\n";

    logger.setLevel(logging.DEBUG)
    filelog.setLevel(logging.DEBUG)
    console.setLevel(logging.DEBUG)
    maillog.setLevel(logging.ERROR)
    phplog.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.addHandler(filelog)
    logger.addHandler(maillog)
    logger.addHandler(phplog)
    return logger


def sanitize(string):
    """ replace all non-ascii chars with _ """
    string=string.replace("ü","ue").replace("ä","ae").replace("ö","oe").replace("ß","ss")
    return ''.join([i if ord(i) < 128 else '_' for i in string])


def folderInfo(path):
    """ get total size and file count in a directory """
    size = 0
    filecount = 0
    for root, _, files in os.walk(path):
        fullpath = os.path.join(path, root)
        for fname in files:
            fullname=os.path.join(fullpath, fname)
            if os.path.isfile(fullname):
                filecount += 1
                size += os.path.getsize(fullname)
    return (size, filecount)

def int2base(num,b,numerals='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'):
    if num == 0: return numerals[0]
    return int2base(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]

def getMac():
    from uuid import getnode
    return getnode()
def getInternalIP():
    return socket.inet_aton(socket.gethostbyname(socket.gethostname()))
def getExternalIP():
    return socket.inet_aton(urllib.request.urlopen("http://api.ipify.org").read().decode('ascii'))

def waitForNetwork():
    """ waits for an internet connection """
    while True:
        try:
            urllib.request.urlopen("http://google.com")
            break
        except urllib.error.URLError:
            time.sleep(10)

lastIDgetTime=datetime.datetime(1,1,1)
lastID="?/?/?"
def getIdentification():
    """ return a string containing external, internal ips and mac address """
    global lastID,lastIDgetTime
    import struct,base64
    now=datetime.datetime.now()
    if (now-lastIDgetTime).total_seconds()>60*60:
        # cache for one hour
        lastIDgetTime=now
        try: lastID = base64.urlsafe_b64encode(struct.pack(">Q",getMac())[2:]+getInternalIP()+getExternalIP()).decode('ascii')
        except: lastID = "Unknown"
    return lastID

def ntpTimeWait():
    """ wait for the new millenium (raspberry does not have hardware clock) """
    while(datetime.date.today().year < 2000):
        time.sleep(1)

def formatdict(sourceDict, replacementDict):
    """ 
    formats all strings in a dict using the other values in the dict 
    example: {a:"test",b:"/root/{a}"} becomes {a:"test",b:"/root/test"}
    """
    for key,value in sourceDict.items():
        if type(value) == dict:
            formatdict(value,replacementDict)
        if type(value) == str:
            sourceDict[key] = value.format(**replacementDict)

def mail(config, message, subject="Automated Mail", contentType="text/plain"):
    """ send an automated email """
    smtpconfig = config['smtp']
    subject = config['templates']['subject'].format(subject=subject,device=config['devicename'])
    email = MIMEText(message + config['templates']['footer'].format(device=config['devicename'],identification=getIdentification()),"plain","utf-8")
    email['To']=Header("{0} <{1}>".format(
            smtpconfig["to"]["name"], smtpconfig["to"]["mail"]))
    email['From']=Header("{0} <{1}>".format(
            smtpconfig["from"]["name"], smtpconfig["from"]["mail"]))
    email["Subject"]=Header(subject)
    try:
        if smtpconfig['usessl']:
            session = smtplib.SMTP_SSL(smtpconfig['server'], smtpconfig['port'])
        else: session = smtplib.SMTP(smtpconfig['server'], smtpconfig['port'])
        session.login(smtpconfig['username'], smtpconfig['password'])
        session.sendmail(smtpconfig["from"]["mail"],
                         smtpconfig["to"]["mail"],
                         email.as_string().encode("utf-8"))
        session.quit()
    except smtplib.SMTPException:
        import traceback,logging
        log=logging.getLogger(config['devicename'])
        log.warn("Could not send email|"+traceback.format_exc())


class MailStream:
    """ a stream for logging to smtp """
    buffer = ""
    config = None

    def __init__(self, config):
        self.config = config

    def write(self, content):
        """ write to buffer """
        self.buffer += content

    def flush(self):
        """ flush buffer, send mail if non-empty """
        self.buffer = self.buffer.strip()
        if len(self.buffer) > 0:
            mail(self.config, self.buffer, subject="Error occurred")
        self.buffer = ""

class PHPUploadStream:
    """ a stream for logging to smtp """
    buffer = ""
    older=[]
    logapiurl = None
    config = None

    def __init__(self, config):
        self.config = config
        self.logapiurl = config['logapiurl']

    def write(self, content):
        """ write to buffer """
        self.buffer += content

    def flush(self):
        """ flush buffer, send mail if non-empty """
        if len(self.buffer) > 1:
            try:
                self.send(self.older+[self.buffer])
                self.older=[]
            except Exception as e:
                print(e)
                self.older += [ self.buffer ]

        self.buffer = ""

    def send(self,messages):
        for message in messages:
            data = urllib.parse.urlencode({'logdata':message.encode('utf-8')})
            response = urllib.request.urlopen(
                    self.logapiurl,
                    data=data.encode('utf-8'),
                    timeout=15).read().decode('utf-8')
            if response[0] != 's':
                print('log server answered with '+response)


