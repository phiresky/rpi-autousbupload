"""
handles recursive ftp uploading
"""
import logging
import os
import util
import datetime

import ftputil

def findDirname(host, basename):
    dirlist = host.listdir(".")
    dirname = basename
    curint = 1
    while dirname in dirlist:
        curint+=1
        dirname = basename + "-" + str(curint)
    return dirname


def uploadDir(config, localroot, label):
    log = logging.getLogger(config['devicename'])

    log.info("scanningFiles")
    totalsize, totalcount = util.folderInfo(localroot)
    begintime = datetime.datetime.now()
    log.info("beginUpload|{localroot}|{label}|{filecount}|{bytecount}.".format(
        localroot=localroot,label=label,filecount=totalcount, bytecount=totalsize))
    util.mail(config, 
            config['templates']['beginUpload']['body'].format(
                filecount=totalcount, megabytes=round(totalsize/1024/1024,1)),
            subject=config['templates']['beginUpload']['subject'])



    ftpconfig = config['ftp']
    log.debug("Connecting to " + ftpconfig['server'])
    host=ftputil.FTPHost(ftpconfig['server'],
                    ftpconfig['username'],
                    ftpconfig['password'])

    host.makedirs(ftpconfig['rootpath'])
    host.chdir(ftpconfig['rootpath'])
    begintime = datetime.datetime.now()
    rootdirname = findDirname(host, begintime.strftime(
        "%Y-%m-%d"))
    host.makedirs(rootdirname)
    host.chdir(rootdirname)
    remoteroot = host.getcwd()
    host.synchronize_times()
    filecount = 0
    bytecount = 0
    statuslogcount=config['uploadlogcount']
    statuslogstatus=-1

    def logFileProgress(info):
        nonlocal bytecount
        bytecount += len(info)
        #log.debug("Progress: "+str(len(info)))
    for root, dirs, files in os.walk(localroot):
        relroot = os.path.relpath(root, localroot)
        #log.debug("walking "+relroot)
        host.chdir(os.path.join(remoteroot, relroot))
        for dirname in dirs:
            host.mkdir(dirname)
        for fname in files:
            osfname=os.path.join(root,fname)
            if not os.path.isfile(osfname): continue
            filecount += 1
            log.debug("uploading " + os.path.join(relroot, fname))
            try:
                host.upload_if_newer(osfname,
                           fname.encode('utf-8'),
                           callback=logFileProgress)
            except (ftputil.FTPOSError,OSError) as e:
                log.warn("Error while uploading "+osfname+", continuing upload."+e)
            if filecount*statuslogcount//totalcount != statuslogstatus:
                statuslogstatus=filecount*statuslogcount//totalcount
                log.info("uploadProgress|{}/{}|{}/{}".format(filecount,totalcount,bytecount,totalsize))

    endtime = datetime.datetime.now()
    totaltime = str(datetime.timedelta(seconds=int((endtime-begintime).total_seconds())))
    host.close()
    log.info("uploadComplete|{filecount}|{bytecount}|{totaltime}".format(**vars()))
    util.mail(config,
        config['templates']['uploadComplete']['body'].format(filecount=filecount,megabytes=round(bytecount/1024/1024,1),duration=totaltime),
        subject=config['templates']['uploadComplete']['subject'])
