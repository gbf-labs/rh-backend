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

class AP7921(Class_PowerSwitch.PowerSwitch):

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
                                        #'sysDescr'              : '1.3.6.1.2.1.1.1.0',
                                        'sysUpTime'             : '1.3.6.1.2.1.1.3.0',
                                        #'sysContact'            : '1.3.6.1.2.1.1.4.0',
                                        'sysName'               : '1.3.6.1.2.1.1.5.0',
                                        #'sysLocation'           : '1.3.6.1.2.1.1.6.0',

                                        'outletCount'    : '1.3.6.1.4.1.318.1.1.12.1.8.0',#'1.3.6.1.4.1.318.1.1.4.5.1.0',  #Num of Outputs     

                                        'loadStatusCurrent'           : '1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1', #phase/bank load measured in tenths of Amps     


                                        'HardwareRev'           : '1.3.6.1.4.1.318.1.1.12.1.2.0',
                                        'FirmwareRev'           : '1.3.6.1.4.1.318.1.1.12.1.3.0',
                                        'DateOfManufacture'     : '1.3.6.1.4.1.318.1.1.12.1.4.0',
                                        'ModelNumber'           : '1.3.6.1.4.1.318.1.1.12.1.5.0',
                                        'SerialNumber'          : '1.3.6.1.4.1.318.1.1.12.1.6.0',

                                        'DeviceRating'          : '1.3.6.1.4.1.318.1.1.12.1.7.0', #max amps
                                        'SerialNumber'          : '1.3.6.1.4.1.318.1.1.12.1.6.0',

                                        'DevicePowerWatts'      : '1.3.6.1.4.1.318.1.1.12.1.16.0',                                        
                                        'DevicePowerVA'         : '1.3.6.1.4.1.318.1.1.12.1.18.0',                                        

                                        }

                #get number of outputs
                snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                outletCount = snmpDevice.readSNMP(self.getDataDict['outletCount'])

                #loop over outlets
                if outletCount is not None:
                        for x in range(1, int(outletCount) + 1):
                                self.getDataDict["outlet" + str(x)] = {}
                                # self.getDataDict["outlet" + str(x)]['ID'] = '1.3.6.1.4.1.1718.3.2.3.1.2.1.1.'  + str(x)
                                self.getDataDict["outlet" + str(x)]['name'] = '1.3.6.1.4.1.318.1.1.12.3.5.1.1.2.'  + str(x)
                                self.getDataDict["outlet" + str(x)]['status'] = '1.3.6.1.4.1.318.1.1.12.3.5.1.1.4.'  + str(x)  #
                                # self.getDataDict["outlet" + str(x)]['controlState'] = '1.3.6.1.4.1.1718.3.2.3.1.10.1.1.' + str(x)  #                              

        def GetDataCleanup(self,result):

                if ("General" in result and "loadStatusCurrent" in result["General"]):                    
                        result["General"]["loadStatusCurrent"] = str(float(result["General"]["loadStatusCurrent"]) / 10.0)

                if ("General" in result and "sysUpTime" in result["General"]):
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
                #if "Command" in command:                        
                #        if (command["Command"] == "rebootoutlet"):
                #                returnValue = self.RebootOutlet(command)                        
                
                return super(self.__class__,self).DoCmd(command, returnValue)                

        def RebootOutlet(self, command):                            
                """
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
                                        res = netsnmp.snmpset(oid, version =2, hostname=self.ipaddr, community='private')

                                        return False
                        else:
                                self.log.printWarning("Given outlet was not a number")
                                return True
                else:
                        self.log.printWarning("No outlet-number was given")
                        return True  
                """
                return True

