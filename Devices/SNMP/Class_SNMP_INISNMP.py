import Class_SNMP
# import MySQLdb
import warnings
import sys
import os
import time
import socket
from parse import *
import re

import lib_Log
import lib_Parsing
import lib_SSH
from pexpect import pxssh

class SNMPV2(Class_SNMP.SNMP):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()

                self.ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                Dictionary = self.INI.getOption(self.deviceDescr, self.devNumber)
                self.getDataDict = {}
                for Name in Dictionary:
                        if Name.startswith('GET_'):
                                self.getDataDict[Name[4:]] = Dictionary[Name]


                
                
