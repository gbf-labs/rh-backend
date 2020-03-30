import Class_VHF
# import MySQLdb
import warnings
import sys
import os
import time
import paramiko
import socket
from parse import *

import lib_Log
import lib_Parsing
import lib_Telnet
import lib_GPS
from pexpect import pxssh

class Sailor_62xx(Class_VHF.VHF):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
                self.channelList = [
                        (0,1,"PORT-PUBLIC","Duplex"),
                        (3,2,"PORT-PUBLIC","Duplex"),
                        (6,3,"PORT-PUBLIC","Duplex"),
                        (9,4,"PORT-PUBLIC","Duplex"),
                        (12,5,"PORT-PUBLIC","Duplex"),
                        (15,6,"INTERSHIP","Simplex"),
                        (18,7,"PORT-PUBLIC","Duplex"),
                        (21,8,"INTERSHIP","Duplex"),
                        (24,9,"INTERSHIP/PORT","Simplex"),
                        (27,10,"INTERSHIP/PORT","Simplex"),
                        (30,11,"SIMPLEX-PORT","Simplex"),
                        (33,12,"SIMPLEX-PORT","Simplex"),
                        (36,13,"INTERSHIP/PORT","Simplex"),
                        (39,14,"SIMPLEX-PORT","Simplex"),
                        (42,15,"INTERSHIP/PORT","Simplex"),
                        (45,16,"DISTRESS/CALL","Simplex"),
                        (48,17,"INTERSHIP/PORT","Simplex"),
                        (51,18,"PORT-PUBLIC","Duplex"),
                        (54,19,"PORT-PUBLIC","Duplex"),
                        (57,20,"PORT-PUBLIC","Duplex"),
                        (60,21,"PORT-PUBLIC","Duplex"),
                        (63,22,"PORT-PUBLIC","Duplex"),
                        (66,23,"PORT-PUBLIC","Duplex"),
                        (69,24,"PORT-PUBLIC","Duplex"),
                        (72,25,"PORT-PUBLIC","Duplex"),
                        (75,26,"PORT-PUBLIC","Duplex"),
                        (78,27,"PORT-PUBLIC","Duplex"),
                        (81,28,"PORT-PUBLIC","Duplex"),
                        (84,60,"PORT-PUBLIC","Duplex"),
                        (87,61,"PORT-PUBLIC","Duplex"),
                        (90,62,"PORT-PUBLIC","Duplex"),
                        (93,63,"PORT-PUBLIC","Duplex"),
                        (96,64,"PORT-PUBLIC","Duplex"),
                        (99,65,"PORT-PUBLIC","Duplex"),
                        (102,66,"PORT-PUBLIC","Duplex"),
                        (105,67,"INTERSHIP/PORT","Simplex"),
                        (108,68,"SIMPLEX-PORT","Simplex"),
                        (111,69,"INTERSHIP/PORT","Simplex"),
                        (114,70,"DISTRESS/DSC","Simplex"),
                        (117,71,"SIMPLEX-PORT","Simplex"),
                        (120,72,"INTERSHIP","Simplex"),
                        (123,73,"INTERSHIP/PORT","Simplex"),
                        (126,74,"SIMPLEX-PORT","Simplex"),
                        (129,75,"SIMPLEX-PORT","Simplex"),
                        (132,76,"SIMPLEX-PORT","Simplex"),
                        (135,77,"INTERSHIP","Simplex"),
                        (138,78,"PORT-PUBLIC","Duplex"),
                        (141,79,"PORT-PUBLIC","Duplex"),
                        (144,80,"PORT-PUBLIC","Duplex"),
                        (147,81,"PORT-PUBLIC","Duplex"),
                        (150,82,"PORT-PUBLIC","Duplex"),
                        (153,83,"PORT-PUBLIC","Duplex"),
                        (156,84,"PORT-PUBLIC","Duplex"),
                        (159,85,"PORT-PUBLIC","Duplex"),
                        (162,86,"PORT-PUBLIC","Duplex"),
                        (165,87,"SIMPLEX-PORT","Simplex"),
                        (168,88,"SIMPLEX-PORT","Simplex")]

        def Connect(self):
                """
                        Called from FBB-class
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
                        self.FBB = lib_Telnet.Telnet()
                        if self.FBB.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                self.FBB.WaitForCursor(ExpectBegin = "\$")
                                self.log.printInfo("Telnet Successfully logged IN")
                                self.FBB.SetPrompt("$")
                return self.Error
        def Disconnect (self):
                """
                        Called from device-class                        
                """
                self.FBB.CloseConnection()
                        

        def GPS_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("nmea pos")
                        result = lib_Parsing.String_Parse(result,["Lat","Lon"],["latitude","longitude"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Version_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("version f")
                        result = lib_Parsing.String_Parse(result,["version"],["Version"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def RadioAppVariables(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("radioapp variables")
                        result = lib_Parsing.String_Parse(result,["radioAppContext.currentRadioMode","currentChannelType","current_ChID","lastDSC_ChID"],["currentRadioMode","currentChannelType","currentChID","lastDSCChID"])
                        # result["currentCh"] = None
                        # result["currentChDesc"] = None
                        try:
                                if (int(result["currentChID"]) > 399) and (int(result["currentChID"]) < 501):
                                        result["currentCh"] = "P" + str(int(result["currentChID"])-400)

                                else:
                                        for item in self.channelList:
                                                if int(item[0]) == int(result["currentChID"]):
                                                        result["currentCh"] = item[1]
                                                        result["currentChDesc"] = item[2]
                                                        result["transmitMode"] = item[3]
                                                        break
                        except Exception as e: 
                                self.log.printError("ERROR in VHF calculation currenchannel") 
                                self.log.printError( str(e))
                                pass
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
                        Extra = {}
                        try:
                                result = {}
                                
                                        
                                temp = self.GPS_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Version_Extraction()
                                if temp != None:
                                        result.update(temp)

                                temp = self.RadioAppVariables()
                                if temp != None:
                                        result.update(temp)
                                        
                                                                                
                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["General"] = result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False 
                                # import pprint
                                # pprint.pprint(sqlArray)
                                # return None   
                                return sqlArray
                                
                        except Exception as e: 
                                self.log.printError("ERROR in Retreiving FBB Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None



        def DoCmd(self, command = None, returnValue = None):
                if "Command" in command:
                        """
                        if (command["Command"] == "beamswitch"):
                                returnValue = self.BeamSwitch(command)
                        if (command["Command"]  == "beamlock"):
                                returnValue = self.BeamLock()
                        if (command["Command"]  == "newmap"):
                                returnValue = self.NewMap()
                        if (command["Command"]  == "removemap"):
                                returnValue = self.RemoveMap()
                        """
                        pass

                
                return super(self.__class__,self).DoCmd(command, returnValue)



        
        def Reboot(self):
                self.FBB.SendCommandWithReturn2("reset")
                self.Disconnect()                
                return False
        
