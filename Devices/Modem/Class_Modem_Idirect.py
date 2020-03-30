import Class_Modem
# import MySQLdb
import warnings
from parse import *
import sys
import time
import os

import lib_Log
import lib_Telnet
import lib_Parsing

class X5(Class_Modem.Modem):
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

                #try to connect
                if self.Error == False:
                        self.Modem = lib_Telnet.Telnet()
                        if self.Modem.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                self.Modem.ExpectQuestion(Question = ":",Answer = username)
                                self.Modem.ExpectQuestion(Question = ":",Answer = password)
                                #self.Modem.WaitForCursor(ExpectBegin = ">")
                                self.Modem.ExpectQuestion(Question = ">",Answer = "xoff")
                                self.Modem.WaitForCursor(ExpectBegin = ">")
                                self.log.printInfo("Telnet Successfully logged IN")
                return self.Error

        def Disconnect (self):
                """
                        Called from device-class                        
                """
                self.Modem.CloseConnection()

        def Rx_SNR_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "rx snr",ExpectEnd = ">")
                        result = lib_Parsing.String_Parse(result,["rx snr"],["Rx_SNR"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Rx_Power_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "rx power",ExpectEnd = ">",Timeout = 100)
                        result = lib_Parsing.String_Parse(result,["rx power"],["Rx_Power"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Remote_State_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "remotestate",ExpectEnd = ">",Timeout = 100)
                        result = result[result.find('\n')+1:result.rfind('\n')]
                        result = lib_Parsing.String_Parse(result,["txer state" , "rxer lock" , "Modem state" , "link layer state"],["Tx_State","Rx_Lock","Modem_State","Link_State"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Selected_Beam_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "beamselector list",ExpectEnd = ">",Timeout = 100)
                        i = 0
                        b = {}
                        c= {}
                        lines = result.splitlines()
                        for line in lines :
                                a = parse("{Selected_Beam} is currently selected", line)
                                if a != None:
                                        b["Selected_Beam"] = a["Selected_Beam"]
                                a = parse("{Beam} = {Description}", line)
                                if a != None:
                                        if a["Beam"] == b["Selected_Beam"]:
                                                b["Selected_Beam_Description"] = a["Description"]
                                        else:
                                                pass
                        result = self.Available_Beam_Extraction(result)
                        if b != None:
                                        result.update(b)

                        return result

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def Available_Beam_Extraction(self,result):
                if self.Error == False:
                        result = result[result.find('\n')+1:result.rfind('\n')]

                        temp = ""
                        Beams = {}
                        #result = string.split(result,'\n')
                        result = result.splitlines()
                        for line in result:
                                if (line [0:5] != "[RMT:") :
                                        temp = temp + line + "\n"
                                        a = parse("{Beam} = {Description}", line)
                                        if a != None:
                                                Beams["Beam[" + a["Beam"] + "]"] = a["Description"]
                        return Beams




        def GPS_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "latlong",ExpectEnd = ">",Timeout = 10)
                        result = lib_Parsing.String_Parse(result,["latlong"],["GPS"])
                        b = parse("{Latitude} {LatitudeDirection} {Longitude} {LongitudeDirection}", result["GPS"])
                        result = {}
                        if b == None:
                                return result
                        else:
                                longitude = float(b["Longitude"])
                                if b["LongitudeDirection"].upper() == 'W' :
                                        longitude = longitude * -1
                                result["Longitude"] = format(longitude, '.5f')

                                latitude = float(b["Latitude"])
                                if b["LatitudeDirection"].upper() == 'S' :
                                        latitude = latitude * -1
                                result["Latitude"] = format(latitude, '.5f')
                                # import pprint
                                # pprint.pprint(result)
                        return result

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Falcon_version_Extraction(self):
                if self.Error == False:
                        temp = self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "packages",ExpectEnd = ">",Timeout = 10)
                        result = {}
                        for line in temp.splitlines():
                                x = line.lower().find("_rmt")
                                if (x > 3):

                                        result["ModemType"] = line[:x].strip()
                                        y = line.lower().find("version:")
                                        if (y > 0):
                                                result["Falcon_Version"] = line[y+8:].strip()
                                        break
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Uptime_Extraction(self):
                if self.Error == False:
                        c = {}
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "uptime",ExpectEnd = ">",Timeout = 10)
                        a = lib_Parsing.String_Parse(result,["application uptime"],["Application_Uptime"])
                        if not "Application_Uptime" in a:
                                return c
                        result = lib_Parsing.TimeSting_To_Sec(a["Application_Uptime"])
                        c["Application_Uptime"] = result
                        return c
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def OptionsFile_Extraction(self):
                if self.Error == False:
                        result =  self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "options show",ExpectEnd = ">")
                        temp = {}
                        temp1 = lib_Parsing.String_Parse(result,["modem_sn"],["Serial_Number"],Section = "OPTIONS_FILE")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["up_translation","down_translation"],["Up_Translation","Down_Translation"],Section = "FREQ_TRANS")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["vid"],["VLAN"],Section = "VLAN")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["hunt_frequency"],["Hunt_Frequency"],Section = "SATELLITE")
                        if temp1 != None:
                                temp.update(temp1)
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def RXIF_Calculation(self,array):
                if self.Error == False:
                        temp = {}
                        if not "Down_Translation" in array or not "Hunt_Frequency" in array:
                                return temp

                        result = float(array["Down_Translation"]) + float(array["Hunt_Frequency"])
                        temp["Rx_IfFreq"] = result
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Print_Values(self,result):
                for key,value in result.items():
                        print("%s = %s" % (key,value))

        def GetData(self):
                """
                        Called from device-class                        
                """
                if self.Error == False:
                        Extra = {}
                        try:
                                result = {}
                                temp = self.Rx_SNR_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Rx_Power_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Remote_State_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Selected_Beam_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.GPS_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Falcon_version_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Uptime_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.OptionsFile_Extraction()
                                if temp != None:
                                        result.update(temp)
                                temp = self.RXIF_Calculation(result)
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
                                self.log.printError("ERROR in Retreiving Modem Data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)


        def DoCmd(self, command = None, returnValue = None):
                if "Command" in command:

                        if (command["Command"] == "beamswitch"):
                                returnValue = self.BeamSwitch(command)
                        if (command["Command"]  == "beamlock"):
                                returnValue = self.BeamLock()
                        if (command["Command"]  == "newmap"):
                                returnValue = self.NewMap()
                        if (command["Command"]  == "removemap"):
                                returnValue = self.RemoveMap()

                
                return super(self.__class__,self).DoCmd(command, returnValue)

        def BeamSwitch(self,command):
                if "Option" in command:
                        #isinstance(command["Option"],( int, long )):
                        if command["Option"].isdigit():
                                Command = "beamselector switch %s -f" % command["Option"]
                                self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = Command,ExpectEnd = ">")
                                self.log.printInfo("Successfully switched to beam %s" % command["Option"])
                                self.Disconnect()
                                return False 
                        self.log.printWarning("Given beam was not a number")
                else:
                        self.log.printWarning("No beamnumber was given")
                        return True                  

        def RemoveMap(self):
                #Dangerous, removing maplet can lead to bad beam balancing
                self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "map delete maplet",ExpectEnd = ">")
                self.log.printInfo("Successfully removed maplet")
                self.Disconnect()
                return False


        def NewMap(self):
                self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "beamselector newmap",ExpectEnd = ">")
                self.log.printInfo("Successfully requested new map")
                self.log.printInfo("It can take a few minutes before the new maplet is downloaded")
                self.Disconnect()
                return False


        def BeamLock(self):
                beam = self.Selected_Beam_Extraction()
                Command = "beamselector lock %s" % beam["Selected_Beam"]
                self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = Command,ExpectEnd = ">")
                self.log.printInfo("Successfully locked current beam '%s' (%s)" % (beam["Selected_Beam_Description"],beam["Selected_Beam"]))
                self.Disconnect()
                return False


        def Reboot(self):
                self.Modem.SendCommandWithReturn(ExpectBegin = ">",Command = "reset board",ExpectEnd = ">")
                self.Disconnect()                
                return False

        def __del__(self):
                pass


class X7(X5):
       pass
