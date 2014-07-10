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
    host._session.set_debuglevel(1)
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
    statusloginterval=config['maxlogdelay']
    statuslogstatus=-1
    lastlogdate=begintime
    failed_files=[]

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
        hostroot = os.path.normpath(os.path.join(remoteroot, util.sanitize(relroot)))
        host.chdir(hostroot)
        if (datetime.datetime.now()-lastlogdate).total_seconds() > statusloginterval:
            # log every 5 minutes
            lastlogdate=datetime.datetime.now()
            logProgress()

        for dirname in dirs:
            dirname=util.sanitize(dirname)
            print("checkdir:"+hostroot+"->"+dirname)
            if not host.path.isdir(dirname): host.mkdir(dirname)
        for fname in files:
            localfname=os.path.join(root,fname)
            if not os.path.isfile(localfname): continue
            hostfname=os.path.join(hostroot,util.sanitize(fname))
            uploadedfiles += 1
            log.debug("uploading " + os.path.join(relroot, fname))
            try:
                uploaded = host.upload_if_newer(localfname,
                           util.sanitize(fname),
                           callback=chunkCallback)
                if not uploaded:
                    log.debug("tmp|skipped file "+localfname)
                    uploadedbytes+=os.path.getsize(localfname)
                    skippedfiles += 1
            except (ftputil.error.FTPOSError,OSError,IOError) as e:
                failed_files.append((localfname,hostfname))
                #log.warn("Error while uploading "+relfname+"|"+traceback.format_exc())

    if len(failed_files)>0: 
        log.warn("failedFiles|"+[local+"->"+remote for local,remote in failed_files])
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
