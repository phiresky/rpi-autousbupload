TODO
---


- sends a mail at beginning and finish or error of upload
- sends log messages to a log server on startup, beginning of upload, percentiles of upload and every 5 minutes
- automatically pulls from github repo on start

dependencies
---
* git
* python3
* python3-pyudev
* python ftputil

installation
---
only tested on [raspbian darkbasic](http://www.linuxsystems.it/raspbian-wheezy-armhf-raspberry-pi-minimal-image/)

as root:

	rm -v /etc/ssh/ssh_host_*
	dpkg-reconfigure openssh-server
	useradd -m uploaduser
	passwd uploaduser
	apt-get update 
	apt-get dist-upgrade
	raspi-config
	apt-get install curl git rpi-update usbmount python3 python3-pyudev python3-pip
	pip-3.2 install ftputil
	sudo curl -L --output /usr/bin/rpi-update https://raw.githubusercontent.com/Hexxeh/rpi-update/master/rpi-update && sudo chmod +x /usr/bin/rpi-update
	rpi-update
	reboot
	vim /etc/usbmount/usbmount.conf # add 'ntfs ntfs-3g' to FILESYSTEMS

as uploaduser:

	git clone https://github.com/phiresky/rpi-autousbupload # must be https for auto updating
	cd rpi-autousbupload
	cp config.json{.sample,}
	vim config.json
	crontab -e # add @reboot /home/uploaduser/rpi-autousbupload/main.py




