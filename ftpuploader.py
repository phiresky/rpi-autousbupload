"""
handles recursive ftp uploading
"""
import logging
import os
import util
import datetime
import traceback

import ftputil

def findDirname(host, basename):
    dirlist = host.listdir(".")
    dirname = basename
    curint = 1
    while dirname in dirlist:
        curint+=1
        dirname = basename + "-" + str(curint)
    return dirname


def uploadDir(config, devicename, localroot, label):
    log = logging.getLogger(config['devicename'])

    log.info("scanningFiles")
    totalbytes, totalcount = util.folderInfo(localroot)
    begintime = datetime.datetime.now()
    log.info("uploadBegin|{localroot}|{label}|{filecount}|{bytecount}".format(
        localroot=localroot,label=label,filecount=totalcount, bytecount=totalbytes))
    util.mail(config, 
            config['templates']['uploadBegin']['body'].format(
                filecount=totalcount, megabytes=round(totalbytes/1024/1024,1)),
            subject=config['templates']['uploadBegin']['subject'])



    ftpconfig = config['ftp']
    log.debug("Connecting to " + ftpconfig['server'])
    try:
        host=ftputil.FTPHost(ftpconfig['server'],
                    ftpconfig['username'],
                    ftpconfig['password'])
    except ftputil.error.FTPOSError:
        log.exception("Could not connect to FTP Server|"+traceback.format_exc())
        return
    superrootpath=ftpconfig['rootpath']
    host.makedirs(superrootpath)
    host.chdir(superrootpath)
    superrootpath = host.getcwd()
    begintime = datetime.datetime.now()
    rootdirname = begintime.strftime("%Y-%m-%d")
    host.makedirs(rootdirname + "-incomplete")
    host.chdir(rootdirname + "-incomplete")
    remoteroot = host.getcwd()
    host.synchronize_times()
    uploadedfiles = 0
    uploadedbytes = 0
    skippedfiles = 0
    statuslogcount=config['uploadlogcount']
    statuslogstatus=-1
    lastlogdate=begintime
    def logProgress():
        nonlocal uploadedfiles,totalcount,uploadedbytes,totalbytes
        log.info("uploadProgress|{uploadedfiles}/{totalcount}|{uploadedbytes}/{totalbytes}".format(**vars()))

    def chunkCallback(info):
        nonlocal uploadedbytes,statuslogcount,totalbytes,statuslogstatus,uploadedfiles,totalcount
        uploadedbytes += len(info)
        curstatus = uploadedbytes*statuslogcount//totalbytes
        if curstatus != statuslogstatus:
            statuslogstatus = curstatus
            logProgress()
    for root, dirs, files in os.walk(localroot):
        relroot = os.path.relpath(root, localroot)
        #log.debug("walking "+relroot)
        host.chdir(os.path.normpath(os.path.join(remoteroot, relroot)))
        if (datetime.datetime.now()-lastlogdate).total_seconds() > 300:
            # log every 5 minutes
            lastlogdate=datetime.datetime.now()
            logProgress()

        for dirname in dirs:
            host.makedirs(dirname)
        for fname in files:
            osfname=os.path.join(root,fname)
            if not os.path.isfile(osfname): continue
            uploadedfiles += 1
            relfname = os.path.join(relroot, fname)
            log.debug("uploading " + relfname)
            try:
                uploaded = host.upload_if_newer(osfname,
                           fname.encode('utf-8'),
                           callback=chunkCallback)
                if not uploaded:
                    log.debug("tmp|skipped file "+osfname)
                    uploadedbytes+=os.path.getsize(osfname)
                    skippedfiles += 1
            except (ftputil.error.FTPOSError,OSError) as e:
                log.warn("Error while uploading "+relfname+"|"+traceback.format_exc())
            except IOError as e:
                log.warn("Could not read file "+relfname+"|"+traceback.format_exc())

    endtime = datetime.datetime.now()
    totaltime = str(datetime.timedelta(seconds=int((endtime-begintime).total_seconds())))
    host.chdir(superrootpath)
    host.rename(remoteroot, findDirname(host, rootdirname))
    host.close()
    if(uploadedfiles<totalcount):
        log.warn(str(totalcount-uploadedfiles-skippedfiles)+" files could not be uploaded|")
        if util.getMountPoint(devicename) == None:
            log.error("Device disappeared before upload completed")
            # might happen because unplugged or not enough power
    log.info("uploadComplete|{uploadedfiles}|{uploadedbytes}|{totaltime}|{skippedfiles}".format(**vars()))
    util.mail(config,
        config['templates']['uploadComplete']['body'].format(filecount=uploadedfiles,megabytes=round(uploadedbytes/1024/1024,1),duration=totaltime),
        subject=config['templates']['uploadComplete']['subject'])
