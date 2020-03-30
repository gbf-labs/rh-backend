import Class_PowerSwitch
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

import lib_SNMP
import netsnmp
# import easysnmp

class Sentry3(Class_PowerSwitch.PowerSwitch):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber                
                self.log.increaseLevel()

                self.ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                self.getDataDict = {
                                        'systemDescription'        : '1.3.6.1.2.1.1.1.0',
                                        'systemUpTime'             : '1.3.6.1.2.1.1.3.0',
                                        'systemContact'            : '1.3.6.1.2.1.1.4.0',
                                        'systemName'               : '1.3.6.1.2.1.1.5.0',
                                        'systemLocation'           : '1.3.6.1.2.1.1.6.0',

                                        'systemVersion'         : '1.3.6.1.4.1.1718.3.1.1.0',
                                        'systemNICSerialNumber'	: '1.3.6.1.4.1.1718.3.1.2.0',
                                        'systemTotalPower'      : '1.3.6.1.4.1.1718.3.1.6.0',

                                        'infeedID'              : '1.3.6.1.4.1.1718.3.2.2.1.2.1.1',
                                        'infeedName'            : '1.3.6.1.4.1.1718.3.2.2.1.3.1.1',
                                        'infeedStatus'          : '1.3.6.1.4.1.1718.3.2.2.1.5.1.1', #0 off, 1 on, 2 offWait, 3 onWait, 4 offError, 5 On Error, 6nocomm, 7 reading, 8 offFuse, 9 onFuse
                                        'infeedLoadValue'       : '1.3.6.1.4.1.1718.3.2.2.1.7.1.1', #in 1/100th of Amps
                                        'infeedLoadHighThresh'  : '1.3.6.1.4.1.1718.3.2.2.1.8.1.1',
                                        'infeedOutletCount'     : '1.3.6.1.4.1.1718.3.2.2.1.9.1.1', #number of outputs
                                        'infeedCapacity'        : '1.3.6.1.4.1.1718.3.2.2.1.10.1.1',
                                        'infeedVoltage'         : '1.3.6.1.4.1.1718.3.2.2.1.11.1.1',
                                        'infeedPower'           : '1.3.6.1.4.1.1718.3.2.2.1.12.1.1',

                                        'towerStatus'           : '1.3.6.1.4.1.1718.3.2.1.1.4.1',   #0 normal, 1 noComm, 2, fanFail, 3 overTemp, 4 nvmfail, 5 outOfBalance
                                        'towerProductSN'        : '1.3.6.1.4.1.1718.3.2.1.1.6.1',
                                        'towerModelNumber'      : '1.3.6.1.4.1.1718.3.2.1.1.7.1',                                        
                                        }

                #get number of outputs
                snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                outletCount = snmpDevice.readSNMP(self.getDataDict['infeedOutletCount'])

                #loop over outlets
                if outletCount is not None:
                        for x in range(1, int(outletCount) + 1):
                                self.getDataDict["outlet" + str(x)] = {}
                                self.getDataDict["outlet" + str(x)]['ID'] = '1.3.6.1.4.1.1718.3.2.3.1.2.1.1.'  + str(x)
                                self.getDataDict["outlet" + str(x)]['name'] = '1.3.6.1.4.1.1718.3.2.3.1.3.1.1.'  + str(x)
                                self.getDataDict["outlet" + str(x)]['status'] = '1.3.6.1.4.1.1718.3.2.3.1.5.1.1.'  + str(x)  #0 off, 1 on, 2 offWait, 3 onWait, 4 offError, 5 On Error, 6nocomm, 7 reading, 8 offFuse, 9 onFuse
                                self.getDataDict["outlet" + str(x)]['controlState'] = '1.3.6.1.4.1.1718.3.2.3.1.10.1.1.' + str(x)  #0 idleOff, 1 idleOn, 2 wakeOff, 3 wakeOn, 4 off, 5 on, 6 lockedOff, 7 lockedOn, 8 reboot, 9 shutdown, 10 pendOn, 11 pendOff, 12 minimumOff, 13 minimumOn, 14 eventOff, 15 eventOn, 16 eventReboot, 17 eventShutdown

        def GetDataCleanup(self,result):
                if "General" in result:
                        if "infeedVoltage" in result["General"]:                                
                                result["General"]["infeedVoltage"] = str(float(result["General"]["infeedVoltage"]) / 10.0)

                        if "infeedLoadValue" in result["General"]:
                                result["General"]["infeedLoadValue"] = str(float(result["General"]["infeedLoadValue"]) / 100.0)

                        if "sysUpTime" in result["General"]:
                                result["General"]["sysUpTime"] = str(float(result["General"]["sysUpTime"]) / 100.0) 

                sqlArray = {}
                sqlArray[self.deviceDescr] = {}
                sqlArray[self.deviceDescr][self.devNumber] = {}
                sqlArray[self.deviceDescr][self.devNumber] = result
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                sqlArray["ReadError"] = False   
                return sqlArray                       


        def DoCmd(self, command = None, returnValue = None):
                if "Command" in command:                        
                        if (command["Command"] == "rebootoutlet"):
                                returnValue = self.RebootOutlet(command)                        
                
                return super(self.__class__,self).DoCmd(command, returnValue)                

        def RebootOutlet(self, command):                            
                if "Option" in command:
                        #isinstance(command["Option"],( int, long )):
                        if command["Option"].isdigit(): 
                                id = int(command["Option"])                               

                                #get number of outputs
                                snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                                outletCount = snmpDevice.readSNMP(self.getDataDict['infeedOutletCount'])

                                if outletCount is not None:
                                        outletCount = int(outletCount)

                                if id > 0 and id <= outletCount:  
                                        self.log.printInfo("Rebooting outlet %s" % id)
                                        #outletControlAction 1.3.6.1.4.1.1718.3.2.3.1.11.1.1.1-8
                                        # readWrite ! - 0 none, 1 on, 2 off, 3 reboot
                                        oid = netsnmp.Varbind('.1.3.6.1.4.1.1718.3.2.3.1.11.1.1.' + str(id),'','3','INTEGER')
                                        res = netsnmp.snmpset(oid, Version=2, DestHost=self.ipaddr, Community='private')
                                        # res = netsnmp.snmpset(oid, version=2, hostname=self.ipaddr, community='private')

                                        return False
                        else:
                                self.log.printWarning("Given outlet was not a number")
                                return True
                else:
                        self.log.printWarning("No outlet-number was given")
                        return True  

