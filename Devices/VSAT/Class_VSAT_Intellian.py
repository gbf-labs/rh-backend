import Class_VSAT
# import MySQLdb
import warnings
import sys
import os
import time
import paramiko
import Class_VSAT
import socket
from parse import *
import re

import lib_Log
import lib_Parsing
import lib_SSH
import lib_SNMP
from pexpect import pxssh

class Vxxx_IARM(Class_VSAT.VSAT):

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
                        Called from device class
                        returns True if failed
                """
                
                #get vars out of INI
                username = self.INI.getOption(self.deviceDescr, self.devNumber, "USER")
                password = self.INI.getOption(self.deviceDescr, self.devNumber, "PASSWORD")
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "SSHPORT")

                #check ini vars
                if None in (username, password, ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: User (= %s), Password (= %s), IP (= %s) and/or Port (= %s) is missing in INI-Files" % (username, password, ipaddr, port))

                #connect
                if self.Error == False:
                        self.SSH = lib_SSH.SSH()
                        self.SSH.SetPrompt(Prompt = ">")
                        if self.SSH.OpenConnection(username,password,ipaddr,port):
                                self.Error = True
                        return self.Error
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                
        def Get_iARM(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show iARM version",Method=1)
                        result = lib_Parsing.String_Parse(result,["Active File System Version"],["iARM"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        
        def Get_BucTemp(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show buc temperature",Method=1)
                        result = lib_Parsing.String_Parse(result,["BUC TEMPERATURE"],["BUCTemperature"])
                        if result == None:
                                return None
                        else:
                                try:
                                        temp = parse("{temp} deg. C",result["BUCTemperature"])
                                        result["BUCTemperature"] = temp["temp"]
                                        return result
                                except:
                                        self.log.printWarning("Could not Parse %s" % result["BUCTxPower"])
                                        return None
                                
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                
        def Get_BucTxPower(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show buc tx power",Method=1)
                        result = lib_Parsing.String_Parse(result,["BUC TX POWER"],["BUCTxPower"])
                        if result == None:
                                return None
                                
                        else:
                                try:
                                        temp = parse("{temp} dBm",result["BUCTxPower"])
                                        result["BUCTxPower"] = temp["temp"]
                                        return result
                                except:
                                        self.log.printWarning("Could not Parse %s" % result["BUCTxPower"])
                                        return None

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        
        def Get_LinkUptime(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show link uptime",Method=1)                       
                        a = lib_Parsing.String_Parse(result,["Current Modem Lock","Total Uptime"],["CurrentModemLock","TotalUptime"])
                        c = {}
                        if "CurrentModemLock" in a:
                                b = parse("{result} ({inseconds} seconds)", a["CurrentModemLock"])
                                if b != None:
                                        result = b["inseconds"]
                                        c["CurrentModemLock"] = result
                        if "TotalUptime" in a:       
                                b = parse("{result} ({inseconds} seconds)", a["TotalUptime"])
                                if b != None:
                                        result = b["inseconds"]
                                        c["TotalUptime"] = result
                                        c["TotalUptime"] = result
                        return c
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        
        def Get_SatTarget(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show acs position target",Method=1)
                        result = lib_Parsing.String_Parse(result,["Azimuth","Elevation","POL"],["TargetAzimuth","TargetElevation","TargetPOL"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        
        def Get_ACS(self):
                if self.Error == False:
                        temp = {}
                        result = self.SSH.SendCommandWithReturn(Command="show acs",Method=1)
                        temp1 = lib_Parsing.String_Parse(result,["STAB","PCU","ACU"],["STAB","PCU","ACU"],Section = "Current Software Information")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["Antenna Status","AGC/Signal","TX Mode"],["AntennaStatus","AGC","TxMode"],Section = "Antenna Status")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["Relative AZ","Absolute AZ","Elevation","POL"],["RelativeAz","AbsoluteAz","Elevation","POL"],Section = "Current Antenna Position") 
                        if temp1 != None:
                                temp.update(temp1)
                        
                        a = lib_Parsing.String_Parse(result,["Latitude","Longitude"],["Latitude","Longitude"],Section = "GPS")
                        if a != None:
                                c = {}
                                try:
                                        b = parse("{Latitude} {LatitudeDirection}", a["Latitude"])
                                        c["Latitude"] = b["Latitude"]
                                        c["LatitudeDirection"] = b["LatitudeDirection"]
                                        b = parse("{Longitude} {LongitudeDirection}", a["Longitude"])
                                        c["Longitude"] = b["Longitude"]
                                        c["LongitudeDirection"] = b["LongitudeDirection"]
                                except:
                                        c = None
                                if c != None:
                                        temp.update(c)

                        temp1 = lib_Parsing.String_Parse(result,["Heading Device","Heading"],["HeadingDevice","Heading"],Section = "Heading Device")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["Bow Offset"],["BowOffset"],Section = "BOW Offset")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["Longitude","Local Frequency","Tracking Frequency(NBD)","Skew Offset"],["SatelliteLongitude","LNBFreq","TrackingFreq","SkewOffset"],Section = "Satellite Information")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["SIZE","SYSTEM BAND","SYSTEM POL.","ANT NAME","ANT SERIAL","ACU NAME","ACU SERIAL"],["AntennaType","System_Band","System_Polarisation","AntennaName","AntennaSerial","ACUName","ACUSerial"],Section = "System Information")
                        if temp1 != None:
                                temp.update(temp1)
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Get_Blockzones(self):
                if self.Error == False:
                        temp = {}
                        result = self.SSH.SendCommandWithReturn(Command="show acs blockzone",Method=1)
                        for x in range (1,6):
                                result = result.replace("BLOCK ZONE " + str(x),"[BLOCK ZONE " + str(x) + "]")
                        for x in range (1,6):
                                temp1 = lib_Parsing.String_Parse(result,["STATUS","AZ START","AZ END","EL END"],["bz" + str(x) + "Status","bz" + str(x) + "AzStart","bz" + str(x) + "AzEnd","bz" + str(x) + "ElEnd"],Section = "BLOCK ZONE " + str(x))
                                if temp1 != None:
                                        temp.update(temp1)
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                
        def Disconnect (self):
                """
                        Called from device class
                """
                self.SSH.CloseConnection()
                        
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
                                temp = self.Get_ACS()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_iARM()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_BucTemp()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_BucTxPower()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_LinkUptime()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_SatTarget()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_Blockzones()
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
                                self.log.printError("ERROR in Retreiving VSAT Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

class Vxxx_E2S(Class_VSAT.VSAT):

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
                        Called from device class
                        returns True if failed
                """
                
                #get vars out of INI
                username = self.INI.getOption(self.deviceDescr, self.devNumber, "USER")
                password = self.INI.getOption(self.deviceDescr, self.devNumber, "PASSWORD")
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "SSHPORT")

                #check ini vars
                if None in (username, password, ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: User (= %s), Password (= %s), IP (= %s) and/or Port (= %s) is missing in INI-Files" % (username, password, ipaddr, port))

                #connect
                if self.Error == False:
                        self.SSH = lib_SSH.SSH()
                        self.SSH.SetPrompt(Prompt = "#")
                        if self.SSH.OpenConnection(username,password,ipaddr,port):
                                self.Error = True
                        return self.Error
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def LoginCli(self):
                if self.Error == False:
                        self.SSH.CreateSession(Command="int")
                        return 
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Get_CLI(self):
                if self.Error == False:
                        #Heading
                        self.SSH.SendCommandInSession(Command="H")
                        #Position
                        self.SSH.SendCommandInSession(Command="P")
                        #Tracking
                        self.SSH.SendCommandInSession(Command="q")
                        #Status
                        self.SSH.SendCommandInSession(Command="S")
                        #Pol
                        self.SSH.SendCommandInSession(Command="u")
                        #Version
                        self.SSH.SendCommandInSession(Command="V")
                        #GPS
                        self.SSH.SendCommandInSession(Command="?@")
                        #LNB
                        self.SSH.SendCommandInSession(Command="L")
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def LogoutCli(self):
                if self.Error == False:
                        result = self.SSH.CloseSessionWithReturn(Command="exit")
                        result = lib_Parsing.String_Parse(result,["AZ_REL","HEADING","AZ_ABS","EL","POL","IF","STATUS","SIGNAL","TX ENABLE","ENABLE MODE","BLOCK ZONE","POINTING","MODEM LOCK","LNB ROTATE","POL","Detect Level","Tracking Level","Antenna","ACU","WEB","GPS(m)","Local","Band","TX Pol"],["RelativeAz","Heading","AbsoluteAz","Elevation","POL","TrackingFreq","AntennaStatus","AGC","TxMode","EnableMode","BlockZone","Pointing","ModemLock","LNBRotate","POL","DetectLevel","TrackingLevel","PCU","ACU","E2S","GPS","LNBFreq","System_Band","TX_Polarisation"])
                        #Clean GPS
                        gps = result["GPS"].split()
                        length = len(gps[0])
                        direction = gps[0][length-1:length]
                        if direction == "N" or direction == "E" or direction == "S" or direction == "W":
                                result["LatitudeDirection"] = gps[0][length-1:length]
                                result["Latitude"] = gps[0][:length-1]
                                
                        length = len(gps[1])
                        direction = gps[1][length-1:length]
                        if direction == "N" or direction == "E" or direction == "S" or direction == "W":
                                result["LongitudeDirection"] = gps[1][length-1:length]
                                result["Longitude"] = gps[1][:length-1]
                        result.pop("GPS",None)
                        #clean ACU
                        acu = result["ACU"].split()
                        result["ACU"] = acu[0]
                        #clean PCU
                        pcu = result["PCU"].split()
                        result["PCU"] = pcu[0]
                        """        
                        import pprint                       
                        pprint.pprint(result)
                        """
                        temp = {}
                        temp["General"] = result
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)    

        def SNMPRequests(self):   
                result = {}
                if self.Error == False:
                        try:
                                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                                self.getDataDict = {
                                'BlockZones'             : '1.3.6.1.4.1.13745.100.1.1.26.0',
                                }  
                                snmpDevice = lib_SNMP.SNMPv2(ipaddr)
                                BlockZones = snmpDevice.readSNMP(self.getDataDict['BlockZones'])  
                                BlockZones = BlockZones.split(";")
                                

                                i = 1
                                for zone in BlockZones:
                                        result["blockzone" + str(i)] = {}
                                        items = zone.split(",")
                                        result["blockzone" + str(i)]["Status"] = items[0]
                                        result["blockzone" + str(i)]["AzStart"] = items[1]
                                        result["blockzone" + str(i)]["AzEnd"] = items[2]
                                        result["blockzone" + str(i)]["ElEnd"] = items[3]
                                        i += 1
                        except Exception as e:
                                return None
                        return result                     
  
        def Disconnect (self):
                """
                        Called from device class
                """
                self.SSH.CloseConnection()
                        
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
                                self.LoginCli()
                                self.Get_CLI()
                                
                                
                                result = {}
                                
                                temp = self.LogoutCli()
                                if temp != None:
                                        result.update(temp)


                                temp = self.SNMPRequests()
                                if temp != None:
                                        result.update(temp)
                                
                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = {}
                                sqlArray[self.deviceDescr][self.devNumber]= result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False   
                                return sqlArray
                                        
                                
                        except Exception as e: 
                                self.log.printError("ERROR in Retreiving VSAT Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None
        def Reboot(self):
                self.LoginCli()
                self.SSH.SendCommandInSession(Command="RA")
                self.SSH.CloseSessionWithReturn(Command="exit")
                self.Disconnect()                
                return False