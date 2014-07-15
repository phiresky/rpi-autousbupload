rpi-autousbupload
---
Automatically uploads data from usb devices to an ftp server.
Just plug in any USB mass storage device (harddrives, usb-sticks, etc.) and it will automatically upload all files. It will also send an email on start and finish and show progress on a status website: ![screenshot](http://i.imgur.com/xKxw1rE.png)

Originally written for [Lichtathleten](http://lichtathleten.com/) but relatively general purpose.

features
---
- scans for existing usb drives at boot and waits for new devices, uploads files on them to an ftp server
- sends a mail at beginning and finish or error of upload
- sends log messages to a log server on startup, beginning of upload, percentiles of upload and every 5 minutes
- automatically pulls from github repo on start

seems to need about 11MB of memory

dependencies
---
* git
* python3
* python3-pyudev
* python ftputil

installation
---
only tested on [raspbian darkbasic](http://www.linuxsystems.it/raspbian-wheezy-armhf-raspberry-pi-minimal-image/)

as root: ssh root@raspberry-pi
```bash
rm -v /etc/ssh/ssh_host_*
dpkg-reconfigure openssh-server
dpkg-reconfigure tzdata
dpkg-reconfigure locales
useradd -m uploaduser
passwd uploaduser
chsh uploaduser # /bin/bash
passwd root
apt-get update 
apt-get dist-upgrade
apt-get install curl git usbmount python3 python3-pyudev python3-pip ntfs-3g
pip-3.2 install ftputil
curl -L --output /usr/local/bin/rpi-update https://raw.githubusercontent.com/Hexxeh/rpi-update/master/rpi-update && chmod +x /usr/local/bin/rpi-update
rpi-update
vi /etc/usbmount/usbmount.conf # add 'ntfs ntfs-3g' to FILESYSTEMS, and "-fstype=vfat,utf8" to FS_MOUNTOPTIONS
reboot
```
as uploaduser: ssh uploaduser@raspberry-pi
```bash
git clone https://github.com/phiresky/rpi-autousbupload # must be https for auto updating
cd rpi-autousbupload
cp config.json{.sample,}
vi config.json
crontab -e # add @reboot /home/uploaduser/rpi-autousbupload/main.py
```
And done!
Reboot again and it should be waiting for devices.



