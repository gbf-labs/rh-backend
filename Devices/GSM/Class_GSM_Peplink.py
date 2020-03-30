import Class_GSM
# import MySQLdb
import warnings
import sys
import os
import time
import socket
from parse import *
import lib_Log
import lib_Parsing
import lib_SSH
import re

class PepwaveMax(Class_GSM.GSM):
        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
        
        def Connect(self):
                """
                        Called from modem-class
                        returns True if failed
                """
                #get vars out of INI
                username = self.INI.getOption(self.deviceDescr, self.devNumber, "USER")
                password = self.INI.getOption(self.deviceDescr, self.devNumber, "PASSWORD")
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "TELNETPORT")

                #check ini vars
                if None in (username, password, ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: User (= %s), Password (= %s), IP (= %s) and/or Port (= %s) is missing in INI-Files" % (username, password, ipaddr, port))        
                        
                if self.Error == False:
                        self.SSH = lib_SSH.SSH()
                        self.SSH.SetPrompt(Prompt = ">")
                        if self.SSH.OpenConnection(username,password,ipaddr,port):
                                self.Error = True
                        return self.Error
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Get_Uptime(self):
                if self.Error == False:
			command = "get uptime"
                        sshResult = self.SSH.SendCommandWithReturn(Command=command)
			sshResult = sshResult.replace(command, "").strip()
                        seconds = -1
                        data = sshResult.splitlines()
                        for line in data:                                
                                #returns "> get uptime Uptime: 4 days 0 hour 10 minutes"				
                                if line.startswith("Uptime:"):
                                        tempstr = line.replace("Uptime:", "").strip()					
                                        parsed = re.split(" ", tempstr)
                                        prevValue = None
                                        seconds = 0
                                        for value in parsed:
                                                if (prevValue == None):
                                                        prevValue = value
                                                else:
                                                        if (((value == "day") or (value == "days")) and (prevValue.isdigit())):
                                                                seconds += int(prevValue) * 3600 * 24
                                                        if (((value == "hour") or (value == "hours")) and (prevValue.isdigit())):
                                                                seconds += int(prevValue) * 3600
                                                        if (((value == "minute") or (value == "minutes")) and (prevValue.isdigit())):
                                                                seconds += int(prevValue) * 60
                                                        prevValue = value
                        result = {}
                        result["uptime"] = seconds
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Get_Wan2(self):
                if self.Error == False:
                        result = {}
                        sshResult = self.SSH.SendCommandWithReturn(Command="get wan 2")
                        data = sshResult.splitlines()
                        dictValues = {"Connection Name" : "name", "Connection Status" : "status", "Connection Type" : "type", "Connection Method" : "method", "IP Address" : "ip", "Default Gateway" : "gateway", "DNS Servers" : "dns" , "MTU" : "mtu"}
                        for searchStr, valName in dictValues.items():
                                result[valName] = None

                        for line in data:
                                #returns
                                #Connection Name                : Cellular 1
                                #Connection Status              : Standby                      Or "Connected To Proximus"
                                #Connection Type                : Cellular
                                #Connection Method              : DHCP
                                #IP Address                     : 46.179.21.206
                                #Default Gateway                : 46.179.21.205
                                #DNS Servers                    : 80.201.237.239
                                #                                80.201.237.238
                                #MTU                            : 1428
                                for searchStr, valName in dictValues.items():
                                        if line.strip().startswith(searchStr):
                                                tempstr = line.replace(searchStr, "").strip()
                                                value = tempstr.replace(":", "").strip()
                                                if (valName == "status"):
                                                        value = value.replace("Connected to", "").strip()
                                                result[valName] = value

                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def GetData(self):
                if self.Error == False:
                        Error = {}
                        try:
                                result = {}
                                temp = self.Get_Uptime()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_Wan2()
                                if temp != None:
                                        result.update(temp)
                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["General"] = result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False    
                                return sqlArray


                        except Exception as e:
                                self.log.printError("ERROR in Retreiving GSM Data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Error["ReadError"] = True
                                return Error
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
