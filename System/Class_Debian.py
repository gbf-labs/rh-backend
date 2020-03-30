import sys 
import os 
import subprocess
import time
import re

import lib_Log
import lib_Bash

def CheckHostname(INI):
	log = lib_Log.Log(PrintToConsole = True)
	log.printBoldInfo("Check Hostname")
	log.increaseLevel()

	INIHostname  = INI.getOption("INFO","VESSELNAME")
	if INIHostname != None:
		#cleanup hostname for forbidden characters
		INIHostname = re.sub (" ","_",INIHostname)
		INIHostname = re.sub('[^a-zA-Z0-9_.]', '', INIHostname)
		#get hostname
		Hostname = subprocess.check_output(["hostname"])
		Hostname = Hostname.strip().decode('ascii')
		if Hostname != INIHostname:
			log.printWarning("changing hostname from '%s' to '%s'" % (Hostname,INIHostname))

			#adjust /etc/hosts
			CommandString = "sed -ie s/" + Hostname + "/" + INIHostname + "/g /etc/hosts"
			if lib_Bash.Bash(str(CommandString)):
				log.printError("Failed changing '/etc/hosts'")

			#adjust /etc/hostname
			CommandString = "sed -ie s/" + Hostname + "/" + INIHostname + "/g /etc/hostname"
			if lib_Bash.Bash(str(CommandString)):
				log.printError("Failed changing '/etc/hostname'")

			#reboot
			log.printWarning("Warning system will reboot in 20 seconds")
			time.sleep(20)
			os.system("sudo shutdown -r now")
		else:
			log.printInfo("Hostname is still correct")


	
