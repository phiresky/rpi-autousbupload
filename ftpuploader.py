"""
handles recursive ftp uploading
"""
import logging
import os
import util
import datetime
import traceback
import socket
import time

import ftputil

CONNDIEWAIT=5 # time to wait when connection dies

def findDirname(host, basename):
    dirlist = host.listdir(".")
    dirname = basename
    curint = 1
    while dirname in dirlist:
        curint+=1
        dirname = basename + "-" + str(curint)
    return dirname

def connectHost(ftpconfig):
    util.waitForNetwork()
    return ftputil.FTPHost(ftpconfig['server'],
                           ftpconfig['username'],
                           ftpconfig['password'])


def uploadDir(config, devicename, localroot, label):
    log = logging.getLogger(config['devicename'])

    log.info("scanningFiles")
    totalbytes, totalcount = util.folderInfo(localroot)
    log.info("uploadBegin|{localroot}|{label}|{filecount}|{bytecount}".format(
        localroot=localroot,label=label,filecount=totalcount, bytecount=totalbytes))
    util.mail(config,
        config['templates']['uploadBegin']['body'].format(
            filecount=totalcount,
            megabytes=round(totalbytes/1024/1024,1)),
            subject=config['templates']['uploadBegin']['subject'])



    ftpconfig = config['ftp']
    log.debug("Connecting to " + ftpconfig['server'])
    try:
        host = connectHost(ftpconfig)
    except ftputil.error.FTPError:
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
        try:
            host.chdir(hostroot)
        except (socket.error,ftputil.error.FTPError,OSError,IOError) as e:
            log.info("tmp|Connection died(a)|"+traceback.format_exc())
            time.sleep(CONNDIEWAIT)
            host.close()
            host = connectHost(ftpconfig)
            host.chdir(hostroot)

        if (datetime.datetime.now()-lastlogdate).total_seconds() > statusloginterval:
            lastlogdate=datetime.datetime.now()
            logProgress()

        for dirname in dirs:
            dirname=util.sanitize(dirname)
            try:
                host.makedirs(dirname)
            except ftputil.error.PermanentError:
                log.debug("Error(b)|"+traceback.format_exc())
                pass
            except (socket.error,ftputil.error.FTPError,OSError,IOError) as e:
                log.debug("Error(b)|"+traceback.format_exc())
                time.sleep(CONNDIEWAIT)
                host.close()
                host = connectHost(ftpconfig)
                host.chdir(hostroot)
                host.makedirs(dirname)

        for fname in files:
            if (datetime.datetime.now()-lastlogdate).total_seconds() > statusloginterval:
                lastlogdate=datetime.datetime.now()
                logProgress()
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
            except (socket.error,ftputil.error.FTPError,OSError,IOError) as e:
                log.info("tmp|(1)Failed uploading "+localfname+"|"+str(e))
                try:
                    time.sleep(CONNDIEWAIT)
                    host.close()
                    host = connectHost(ftpconfig)
                    host.chdir(hostroot)
                    host.upload(localfname,
                               util.sanitize(fname),
                               callback=chunkCallback)
                except (socket.error,ftputil.error.FTPError,OSError,IOError) as e:
                    log.info("tmp|(2)Failed uploading "+localfname+"|"+str(e))
                    failed_files.append((localfname,hostfname))

    again_failed_files = []
    if len(failed_files)>0: 
        log.info("failedFiles|"+"\n".join([local+"->"+remote for local,remote in failed_files]))
        while True:
            # retry uploading until no more files can be uploaded
            time.sleep(CONNDIEWAIT)
            host.close()
            host = connectHost(ftpconfig)
            for local,remote in failed_files:
                try:
                    host.upload(local,remote,callback=chunkCallback)
                except (socket.error,ftputil.error.FTPError,OSError,IOError) as e:
                    log.info("tmp|Again failed uploading "+localfname+"|"+traceback.format_exc())
                    again_failed_files.append((localfname,hostfname))
            if len(again_failed_files) == len(failed_files):
                break
            else:
                failed_files = again_failed_files
            

    if len(again_failed_files)>0: 
        log.warn("failedFiles|"+"\n".join([local+"->"+remote for local,remote in failed_files]))


    endtime = datetime.datetime.now()
    totaltime = str(datetime.timedelta(seconds=int((endtime-begintime).total_seconds())))
    host.chdir(superrootpath)
    host.rename(remoteroot, findDirname(host, rootdirname))
    host.close()
    if(uploadedfiles<totalcount):
        log.warn(str(totalcount-uploadedfiles)+" files could not be uploaded|")
        if util.getMountPoint(devicename) == None:
            log.error("Device disappeared before upload completed")
            # might happen because unplugged or not enough power
    log.info("uploadComplete|{uploadedfiles}|{uploadedbytes}|{totaltime}|{skippedfiles}".format(**vars()))
    util.mail(config,
        config['templates']['uploadComplete']['body'].format(filecount=uploadedfiles,megabytes=round(uploadedbytes/1024/1024,1),duration=totaltime),
        subject=config['templates']['uploadComplete']['subject'])
