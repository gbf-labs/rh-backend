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
import binascii

class PX2(Class_PowerSwitch.PowerSwitch):

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
                                        'pduManufacturer'       : '1.3.6.1.4.1.13742.6.3.2.1.1.2.1',
                                        'pduModel'              : '1.3.6.1.4.1.13742.6.3.2.1.1.3.1',
                                        'pduSerialNumber'       : '1.3.6.1.4.1.13742.6.3.2.1.1.4.1',
                                        #'pduRatedVoltage'      : '1.3.6.1.4.1.13742.6.3.2.1.1.5.1',
                                        #'pduRatedCurrent'      : '1.3.6.1.4.1.13742.6.3.2.1.1.6.1',
                                        #'pduRatedFrequency'    : '1.3.6.1.4.1.13742.6.3.2.1.1.7.1',
                                        #'pduRatedVA'           : '1.3.6.1.4.1.13742.6.3.2.1.1.8.1',
                                        'OutletCount'           : '1.3.6.1.4.1.13742.6.3.2.2.1.4.1',
                                        'pduName'               : '1.3.6.1.4.1.13742.6.3.2.2.1.13.1',
                                        'pduPower'              : '1.3.6.1.4.1.13742.6.5.2.3.1.6.1.1.5',
                                        'pduVA'                 : '1.3.6.1.4.1.13742.6.5.2.3.1.6.1.1.6',
                                        'pduLineFrequency'      : '1.3.6.1.4.1.13742.6.5.2.3.1.6.1.1.23',
                                        'pduMAC'                : '1.3.6.1.2.1.2.2.1.6.2',
                                        'pduInletCurrent'       : '1.3.6.1.4.1.13742.6.5.2.3.1.6.1.1.1',
                                        'pduInletVoltage'       : '1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.4',
                        
                                        }

                #get number of outputs
                snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                outletCount = snmpDevice.readSNMP(self.getDataDict['OutletCount'])

                #loop over outlets
                if outletCount is not None:
                        for x in range(1, int(outletCount) + 1):
                                self.getDataDict["outlet" + str(x)] = {}
                                self.getDataDict["outlet" + str(x)]['name']     = '1.3.6.1.4.1.13742.6.3.5.3.1.3.1.'  + str(x)
                                self.getDataDict["outlet" + str(x)]['status']   = '1.3.6.1.4.1.13742.6.4.1.2.1.2.1.'  + str(x)  #0 off, 1 on, 2 offWait, 3 onWait, 4 offError, 5 On Error, 6nocomm, 7 reading, 8 offFuse, 9 onFuse
                                self.getDataDict["outlet" + str(x)]['uptime']   = '1.3.6.1.4.1.13742.6.4.1.2.1.4.1.' + str(x)  #0 idleOff, 1 idleOn, 2 wakeOff, 3 wakeOn, 4 off, 5 on, 6 lockedOff, 7 lockedOn, 8 reboot, 9 shutdown, 10 pendOn, 11 pendOff, 12 minimumOff, 13 minimumOn, 14 eventOff, 15 eventOn, 16 eventReboot, 17 eventShutdown

        def GetDataCleanup(self,result):

                if ("General" in result and "pduMAC" in result["General"]):     
                        result["General"]["pduMAC"] = self.converttomac(result["General"]["pduMAC"])
                

                sqlArray = {}
                if result["General"]["pduMAC"] == None:

                        sqlArray["ReadError"] = True   
                        
                else:

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
                                outletCount = snmpDevice.readSNMP(self.getDataDict['OutletCount'])

                                if outletCount is not None:
                                        outletCount = int(outletCount)

                                if id > 0 and id <= outletCount:  
                                        self.log.printInfo("Rebooting outlet %s" % id)
                                        #outletControlAction 1.3.6.1.4.1.1718.3.2.3.1.11.1.1.1-8
                                        # readWrite ! - 0 none, 1 on, 2 off, 3 reboot
                                        oid = netsnmp.Varbind('.1.3.6.1.4.1.13742.6.4.1.2.1.2.1.' + str(id),'','2','INTEGER')
                                        netsnmp.snmpset(oid, Version=2, DestHost=self.ipaddr, Community='RadioHolland')

                                        return False
                        else:
                                self.log.printWarning("Given outlet was not a number")
                                return True
                else:
                        self.log.printWarning("No outlet-number was given")
                        return True  



        def converttomac(self,mac):
                if mac == None:
                        return None
                try:
                        mac = binascii.hexlify(mac)
                        s = ""
                        for i in range(0,12,2):
                            s += mac[i:i+2] + ":"
                        result=s[:-1]
                        return result
                except:
                        return None

