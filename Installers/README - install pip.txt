Install special version of pip to get paramiko >= v2.0
------------------------------------------------------

#wget https://bootstrap.pypa.io/get-pip.py
sudo python ./get-pip.py
sudo apt-get install python-pip
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
sudo pip install cryptography
sudo pip install paramiko
#rm get-pip.py


