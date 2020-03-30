
## Python 2(Installation)
```
sudo apt-get -y install python-pip
sudo apt-get install python-netsnmp
sudo -E pip install pexpect 
sudo pip install -r requirementsV1.txt
sudo apt-get -y install python-requests
sudo apt-get install snmp
sudo apt-get install net-tools
sudo apt-get install vlan

sudo apt-get -y install ntp
sudo reboot # after all are install
```

## Python 3: Run the following
```bash
sudo apt-get -y install python3-pip
sudo apt-get -y install python3-git
sudo apt-get install vlan
sudo apt-get install nmap
sudo apt-get -y install ntp

sudo apt-get -y install libsnmp-dev
sudo apt-get -y install net-tools
sudo apt-get -y install python3-bs4
sudo apt-get install net-tools
sudo apt-get install vlan
sudo apt-get install snmp
sudo -E pip install pexpect 
sudo pip3 install -r requirements.txt

sudo reboot # after all are install

# If snmp is the problem follow the link below
# https://easysnmp.readthedocs.io/en/latest/session_api.html
# https://packages.debian.org/source/stretch/net-snmp


#./System/Class_ReadConfigINI.py

#change ini/ to ./
#	   python/ to ./
```
## To install pip3, run the following commands
```bash
curl http://python-distribute.org/distribute_setup.py | sudo python3
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | sudo python3
```

## SET PYTHON 2/3 DEFAULT [source](https://linuxconfig.org/how-to-change-default-python-version-on-debian-9-stretch-linux)
```bash
ls /usr/bin/python*

update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.5 2

# Please note that the integer number at the end of each command denotes a priority. 
# Higher number means higher priority and as such the /usr/bin/python3.5 version was 
# set in Auto Mode to be a default if no other selection is selected. After executing 
# both above commands your current default python version is /usr/bin/python3.5 due 
# to its higher priority (2):
```