import Class_SATC
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

class TT3027C(Class_SATC.SATC):

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
                                        # 'sysDescr'              : '1.3.6.1.2.1.1.1.0',
                                        'sysUpTime'             : '1.3.6.1.2.1.1.3.0',
                                        }





        def Connect(self):
                """
                        Called from SATC-class
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
                        self.SATC = lib_Telnet.Telnet()
                        if self.SATC.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                self.SATC.WaitForCursor(ExpectBegin = "\$")
                                self.log.printInfo("Telnet Successfully logged IN")
                                self.SATC.SetPrompt("$")
                return self.Error
        def Disconnect (self):
                """
                        Called from device-class                        
                """
                self.SATC.CloseConnection()

        def inmcles(self):
                if self.Error == False:
                        result = {}
                        temp =  self.SATC.SendCommandWithReturn2("inmcles")
                        region = {"44" : "Atlantic Ocean West", "144" : "Atlantic Ocean East", "244" : "Pacific Ocean", "344" : "Indian Ocean"}
                        oceanRegion = re.search(r"NCS id (?P<result>.*)", temp).group("result").strip()
                        if oceanRegion in region:
                               result["currentOceanRegion"] = region[oceanRegion] 
                        final = {}
                        final["General"] = result
                        return final
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def inmcstatus(self):
                if self.Error == False:
                        result = {}
                        temp =  self.SATC.SendCommandWithReturn2("inmcstatus")
                        result["type"] = re.search(r"Transceiver type : (?P<result>.*)", temp).group("result").strip()
                        result["connected"] = re.search(r"Transceiver connected (?P<result>.*)", temp).group("result").strip()
                        result["interfaceVersion"] = re.search(r"Interface software version (?P<result>.*)", temp).group("result").strip()
                        result["serial"] = re.search(r"Serial number (?P<result>.*)", temp).group("result").strip()
                        result["transceiverVersion"] = re.search(r"Transceiver SW version (?P<result>.*)", temp).group("result").strip()
                        result["currentProtocol"] = re.search(r"Current protocol (?P<result>.*)", temp).group("result").strip()


                        regexResult = re.search(r"Position is\s*(?P<lat>[\d|\.]*)(?P<latdir>.)\s*(?P<lon>[\d|\.]*)(?P<londir>.) Valid: (?P<valid>\d*),\s*Origin\s*(?P<origin>.*)", temp)
                        if regexResult != None:
                                if regexResult.group("valid").strip() == "1":
                                        result["latitude"] = regexResult.group("lat").strip()
                                        if result["latitude"][-1] == ".":
                                               result["latitude"] = result["latitude"][:-1]  
                                        result["latitudeDirection"] = regexResult.group("latdir").strip()

                                        result["longitude"] = regexResult.group("lon").strip()
                                        if result["longitude"][-1] == ".":
                                               result["longitude"] = result["longitude"][:-1]
                                        result["longitudeDirection"] = regexResult.group("londir").strip()
                                        result["gpsOrigin"] = regexResult.group("origin").strip()


                        final = {}
                        final["General"] = result
                        return final
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def inmcmob(self):
                if self.Error == False:
                        result = {}
                        temp =  self.SATC.SendCommandWithReturn2("inmcmob")
                        result["mobileNumber"] = re.search(r"Mobil number (?P<result>.*)", temp).group("result").strip()
                        final = {}
                        final["General"] = result
                        return final
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
                                
                                        
                                temp = self.inmcstatus()
                                if temp != None:
                                        result = memory.dict_merge(result,temp)

                                temp = self.inmcmob()
                                if temp != None:
                                        result = memory.dict_merge(result,temp)

                                temp = self.getsnmpinfo()
                                if temp != None:
                                        result = memory.dict_merge(result,temp)

                                temp = self.inmcles()
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
                                self.log.printError("ERROR in Retreiving SATC Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None


        def getsnmpinfo(self):                
                result = {}    

                SNMPDevice = lib_SNMP.SNMPv2(self.ipaddr)

                for keyword in self.getDataDict:
                        if isinstance(self.getDataDict[keyword],dict):
                                result[keyword] = {}
                                for option in self.getDataDict[keyword]:
                                        result[keyword][option] = SNMPDevice.readSNMP(self.getDataDict[keyword][option])
                        else:
                                if not "General" in result:
                                        result["General"] = {}
                                result["General"][keyword] = SNMPDevice.readSNMP(self.getDataDict[keyword])
                result = self.SnmpDataCleanup(result)
                return result


        def SnmpDataCleanup(self,result):
                #if "rPDULoadStatusLoad" in result:
                        #result["rPDULoadStatusLoad"] = str(float(result["rPDULoadStatusLoad"]) / 10.0)
                if (("General" in result) and ("sysUpTime" in result["General"])): 
                        result["General"]["sysUpTime"] = str(float(result["General"]["sysUpTime"]) / 100.0)
                return result



        def DoCmd(self, command = None, returnValue = None):
                #if "Command" in command:                        
                #        if (command["Command"] == "rebootoutlet"):
                #                returnValue = self.RebootOutlet(command)                        
                
                return super(self.__class__,self).DoCmd(command, returnValue)                



