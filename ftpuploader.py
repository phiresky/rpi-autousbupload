"""
handles recursive ftp uploading
"""
import logging
import os
import util
import datetime

from ftputil import FTPUtil


def uploadDir(config, localroot, label):
    log = logging.getLogger(config['devicename'])
    ftpconfig = config['ftp']
    log.debug("Connecting to " + ftpconfig['server'])
    ftputil=FTPUtil(ftpconfig,log)
    ftputil.recursive_mkd_cwd(ftpconfig['rootpath'])
    begintime = datetime.datetime.now()
    rootdirname = begintime.strftime(
        "%Y-%m-%d.%H%M%S")
    remoteroot = ftputil.mkd_cwd(rootdirname)
    log.debug("Scanning files")
    totalsize, totalcount = util.folderInfo(localroot)
    begintime = datetime.datetime.now()
    log.info("beginUpload|{localroot}|{label}|{filecount}|{bytecount}.".format(
        localroot=localroot,label=label,filecount=totalcount, bytecount=totalsize))
    util.mail(config, 
            config['templates']['beginUpload']['body'].format(
                filecount=totalcount, megabytes=round(totalsize/1024/1024,1)),
            subject=config['templates']['beginUpload']['subject'])
    filecount = 0
    bytecount = 0
    statuslogcount=config['uploadlogcount']
    statuslogstatus=0

    def logFileProgress(info):
        nonlocal bytecount
        bytecount += len(info)
        #log.debug("Progress: "+str(len(info)))
    for root, dirs, files in os.walk(localroot):
        relroot = os.path.relpath(root, localroot)
        #log.debug("walking "+relroot)
        ftputil.ftp.cwd(os.path.join(remoteroot, relroot))
        for dirname in dirs:
            ftputil.ftp.mkd(dirname)
        for fname in files:
            osfname=os.path.join(root,fname)
            if not os.path.isfile(osfname): continue
            filecount += 1
            log.debug("uploading " + os.path.join(relroot, fname))
            try:
                ftputil.upload(fileobj=open(osfname, 'rb'),
                           filename=fname,
                           blocksize=1024 * 512,
                           callback=logFileProgress)
            except OSError as e:
                log.exception("Error while uploading "+osfname+", continuing upload")
            if filecount*statuslogcount//totalcount != statuslogstatus:
                statuslogstatus=filecount*statuslogcount//totalcount
                log.info("uploadProgress|{}/{}|{}/{}".format(filecount,totalcount,bytecount,totalsize))

    endtime = datetime.datetime.now()
    totaltime = str(datetime.timedelta(seconds=int((endtime-begintime).total_seconds())))
    log.info("uploadComplete|{filecount}|{bytecount}|{totaltime}".format(**vars()))
    util.mail(config,
        config['templates']['uploadComplete']['body'].format(filecount=filecount,megabytes=round(bytecount/1024/1024,1),duration=totaltime),
        subject=config['templates']['uploadComplete']['subject'])
