"""
waits for usb devices and uploads their contents to an ftp server
"""
import pyudev, time, os
import util, ftpuploader
import logging

class USBWait:
    def __init__(self,config):
        self.config=config
        self.log=logging.getLogger(config['devicename'])


    def handle_usb(self, action, device):
        """
        handle a device plugin event
        """
        if action != 'add':
            return
        devname = device['DEVNAME']
        if device['DEVTYPE'] == "disk":
            # added main disk like /dev/sda, happens before OS scans for partitions
            self.log.debug("Added disk {0}, waiting for partitions".format(devname))
            return
        if device['DEVTYPE'] != "partition":
            return
        # get readable disk name if it exists
        devlabel = device['ID_FS_LABEL'] if 'ID_FS_LABEL' in device else "Unknown"
        self.handle_partition(devname,devlabel)
        
    def handle_partition(self, devname, devlabel="Unknown"):
        self.log.info("addedPartition|{0}|{1}|waiting for mount"
                 .format(devlabel, devname))
        mountpoint = None
        retries = 0
        while mountpoint == None and retries < 10:
            # wait 15 seconds for the OS to automount the drive
            time.sleep(1.5)
            retries += 1
            mountpoint = util.getMountPoint(devname)
        if mountpoint == None:
            self.log.info("Device {0}({1}) was not mounted"
                      .format(devlabel, devname))
            return
        campath = util.relpathjoin(mountpoint, self.config['devicerootpath'])
        if not os.path.exists(campath):
            self.log.info("invalidDevice|Device does not seem to be a fitting drive, " +
                     "aborting (404 "+campath+")")
            return
        try:
            ftpuploader.uploadDir(self.config, campath, devlabel)
        except:
            self.log.exception('Error in ftp uploader')

    def handle_first(self):
        """ scan for devices added before starting the udev monitor """
        for partition in util.getPartitions():
            self.handle_partition("/dev/"+partition)

    def main_loop(self,handleAlreadyMounted=True):
        """ begin the main event loop monitoring devices """
        if handleAlreadyMounted: self.handle_first()
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('block')#,'partition')

        self.log.info("boot|Started USB wait loop")
        for action, device in monitor:
            try:
                self.handle_usb(action,device)
            except KeyboardInterrupt:
                raise
            except:
                self.log.exception("Exception while handling device")

        """observer = pyudev.MonitorObserver(monitor, self.handle_usb)
        observer.start()
        while True:
            time.sleep(10000)"""
