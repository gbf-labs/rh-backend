import Class_AlarmPanel
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
# import netsnmp
import lib_Telnet
import Class_GlobalMemory

class TT6103(Class_AlarmPanel.AlarmPanel):

        def __init__(self, INI, deviceDescr, devNumber):                
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber                
                self.log.increaseLevel()

                self.ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")


        def Connect(self):
                """
                        Called from AlarmPanel-class
                        returns True if failed
                """
                
                #get vars out of INI
                # username = self.INI.getOption(self.deviceDescr, self.devNumber, "USER")
                # password = self.INI.getOption(self.deviceDescr, self.devNumber, "PASSWORD")
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "TELNETPORT")

                #check ini vars
                if None in (ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: IP (= %s) and/or Port (= %s) is missing in INI-Files" % (ipaddr, port))

                #try to connect
                if self.Error == False:
                        self.AlarmPanel = lib_Telnet.Telnet()
                        if self.AlarmPanel.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                self.AlarmPanel.WaitForCursor(ExpectBegin = "\$")
                                self.log.printInfo("Telnet Successfully logged IN")
                                self.AlarmPanel.SetPrompt("$")
                return self.Error
        def Disconnect (self):
                """
                        Called from device-class                        
                """
                self.AlarmPanel.CloseConnection()
                        

        def getSysconf(self):
                if self.Error == False:
                        result = {}
                        temp =  self.AlarmPanel.SendCommandWithReturn2("sysconf")
                        result = lib_Parsing.String_Parse(temp,["Model number","MAC","Serial number"],["type","MAC","serial"])
                        final = {}
                        final["General"] = result
                        return final
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def getAlinfo(self):
                if self.Error == False:
                        result = {}
                        temp =  self.AlarmPanel.SendCommandWithReturn2("alinfo")
                        # result["mobileNumber"] = re.findall(r"\d: (?P<device>\w*) * (?P<IP>[\d|.| ]*)", temp).group("result").strip()
                        matches = re.finditer(r"\d: (?P<device>\w*) * (?P<IP>[\d|.| ]*)", temp)
                        for matchNum, match in enumerate(matches):
                            device = match.group("device").strip()
                            result[device] = {}
                            result[device]["IP"] = match.group("IP").replace(" ", "")
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

                        
        def Print_Values(self,result): 
                if self.Error == False:
                        for key,value in result.items():
                                print("%s = %s" % (key,value))
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        
        
        def GetData(self):
                """
                        Called from device class
                """
                if self.Error == False:
                        memory = Class_GlobalMemory.GlobalMemory()
                        Extra = {}
                        try:
                                result = {}
                                
                                        
                                temp = self.getSysconf()
                                if temp != None:
                                        result = memory.dict_merge(result,temp)

                                temp = self.getAlinfo()
                                if temp != None:
                                        result = memory.dict_merge(result,temp)

                                                     
                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False 
                                # import pprint
                                # pprint.pprint(sqlArray)
                                # return None   
                                return sqlArray
                                
                        except Exception as e: 
                                self.log.printError("ERROR in Retreiving AlarmPanel Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None




        def DoCmd(self, command = None, returnValue = None):
                #if "Command" in command:                        
                #        if (command["Command"] == "rebootoutlet"):
                #                returnValue = self.RebootOutlet(command)                        
                
                return super(self.__class__,self).DoCmd(command, returnValue)                



