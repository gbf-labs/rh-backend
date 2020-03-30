import Class_FBB
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

class FBB_500(Class_FBB.FBB):

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
                        Called from FBB-class
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

                #try to connect
                if self.Error == False:
                        self.FBB = lib_Telnet.Telnet()
                        if self.FBB.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                self.FBB.ExpectQuestion(Question = ":",Answer = username,End = "\n\r")
                                self.FBB.ExpectQuestion(Question = ":",Answer = password,End = "\n\r")
                                self.FBB.WaitForCursor(ExpectBegin = "\$")
                                self.log.printInfo("Telnet Successfully logged IN")
                                self.FBB.SetPrompt("$")
                return self.Error
        def Disconnect (self):
                """
                        Called from device-class                        
                """
                self.FBB.CloseConnection()
                        
        def LinkStatus_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("showLinkStatus")
                        result = lib_Parsing.String_Parse(result,["Link status"],["Link_Status"])
                        List = result["Link_Status"].split()
                        result = ""
                        for data in List:
                                result += data + "\n"
                        result = lib_Parsing.String_Parse(result,["Port1","Port2","Port3","Port4"],["Port1","Port2","Port3","Port4"])          
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def GPS_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("ALgetGpsData")
                        result = lib_Parsing.Cut_Multiline_String(result,Begin = "Copy of last", End = "ECEF")
                        result = lib_Parsing.String_Parse(result,["Current Fix Status","Satellites","hmsl"],["GPS_Fix","GPS_Satellites","SealevelHeight"])
                        result["SealevelHeight"] = result["SealevelHeight"].split()[0]
                        result["GPS_Satellites"] = result["GPS_Satellites"].split()[0]
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def SysState_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("sys_state")
                        result = lib_Parsing.Cut_Multiline_String(result,Begin = "---", End = "---")
                        result = lib_Parsing.String_Parse(result,["BDU state","ADU state","MSG state"],["BDU_State","ADU_State","MSG_State"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def SatInfo_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("mmisatinfo  stat")
                        result = lib_Parsing.Cut_Multiline_String(result,Begin = "Satellite status")
                        result = lib_Parsing.String_Parse(result,["Connection status","Satellite name","Satellite ID","Satellite longitude","Spotbeam type","Spotbeam ID","Pointing elevation","Pointing azimuth","Signal Quality (C/N0)","Vessel latitude","Vessel longitude"],["Status","Sat_Name","Sat_ID","Sat_Longitude","Spotbeam_Type","Spotbeam_ID","Elevation","AbsoluteAz","Signal","Latitude","Longitude"])
                        result["Elevation"] = result["Elevation"].split()[0]
                        result["AbsoluteAz"] = result["AbsoluteAz"].split()[0]
                        result["Signal"] = result["Signal"].split()[0]
                        data = parse("{none}({gps})", result["Latitude"])
                        dir = parse('{none}" {dir}',data["gps"])
                        result["LatitudeDir"] = dir["dir"]
                        Latitude = data["gps"]
                        
                        data = parse("{none}({gps})", result["Longitude"])
                        dir = parse('{none}" {dir}',data["gps"])
                        result["LongitudeDir"] = dir["dir"]
                        Longitude = data["gps"]
                        temp = Latitude + " " + Longitude
                        gps = lib_GPS.parse_dms(temp)
                        result["Latitude"] = gps[0]
                        result["Longitude"] = gps[1]
                        
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Version_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("ver")
                        result = lib_Parsing.String_Parse(result,["Software"],["Software"])
                        data = result["Software"].split()[0]
                        result["Software"] = data[:len(data)-1]
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Temp_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("temp")
                        result = lib_Parsing.Cut_Multiline_String(result,Begin = "sensor")
                        lines = result.split('\n')
                        result = {}
                        for line in lines:
                                parts = line.split()
                                if parts[0] == "acm":
                                        result["ACM_Temp"] = parts[2]
                                        if parts[5] == "0":
                                                result["ACM_Alarm"] = False
                                        else:
                                                result["ACM_Alarm"] = True
                                if parts[0] == "hpa":
                                        result["HPA_Temp"] = parts[2]
                                        if parts[5] == "0":
                                                result["HPA_Alarm"] = False
                                        else:
                                                result["HPA_Alarm"] = True
                                if parts[0] == "mainboard":
                                        result["Mainboard_Temp"] = parts[2]
                                        if parts[5] == "0":
                                                result["Mainboard_Alarm"] = False
                                        else:
                                                result["Mainboard_Alarm"] = True
                                                
                        
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Uptime_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("uptime")
                        data = result.split()
                        data.pop(0)
                        data.pop(0)
                        Dataparts = len(data)
                        result = 0
                        i = 0
                        while i < Dataparts:
                                
                                if data[i].lower() == "days" or data[i].lower() == "day":
                                        result += float(data[i-1]) * 24 * 60 * 60
                                        if i + 2 == Dataparts:
                                                timestring = data[i+1]
                                                timestring = timestring.replace(":", " ")
                                                timestring = timestring.split()
                                                timestringparts = len(timestring)
                                                if timestringparts == 3:
                                                        result += float(timestring[0]) * 60 * 60
                                                        result += float(timestring[1]) * 60 
                                                        result += float(timestring[2]) 
                                                        break
                                i += 1
                        data = {}
                        data["Uptime"] = result
                        return data
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Network_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("ifconfig")
                        result = lib_Parsing.String_Parse(result,["ip","netmask","mac"],["IP","Netmask","MAC"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Serial_Extraction(self):
                if self.Error == False:
                        result =  self.FBB.SendCommandWithReturn2("sip g")
                        result = lib_Parsing.Cut_Multiline_String(result,Begin = "SIP user data base", End = "i: 1 name")
                        data = result.split()
                        read = False
                        result = None
                        for part in data:
                                if read:
                                        result = {}
                                        result["Serial"] = part
                                        break
                                if part == "realm:":
                                        read = True

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
                                temp = self.LinkStatus_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.GPS_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.SysState_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.SatInfo_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Version_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Temp_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Uptime_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Network_Extraction()
                                if temp != None:
                                        result.update(temp)
                                        
                                temp = self.Serial_Extraction()
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
        
