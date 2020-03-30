import Class_Mediator
import time
import warnings
import sys
import os
import re

from parse import *

import lib_Log
import lib_Parsing
import lib_WebScraping
import lib_GPS
from pexpect import pxssh

class Seatel_Mediator(Class_Mediator.Mediator):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
                self.IP = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"IP")
                if self.IP is None:
                        self.log.printWarning("IP for %s%s not set"%(self.deviceDescr,self.devNumber) )
                        self.Error = True
                self.User = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"USER")
                if self.User is None:
                        self.log.printWarning("User for %s%s not set"%(self.deviceDescr,self.devNumber) )
                        self.Error = True
                self.Password = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"PASSWORD")
                if self.Password is None:
                        self.log.printWarning("Password for %s%s not set"%(self.deviceDescr,self.devNumber) )
                        self.Error = True




                self.Port = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"HTTPPORT")        
                if self.Port is None:
                        self.Port = ""
                else:
                        self.Port = ":" + self.Port

                self.CommIf = ""
        
                        
        def ScrapeMainWebpage(self):
                 
                if self.Error == False:
                
                        result = {}
                        Scrape = lib_WebScraping.WebScraping()

                        URL = "http://" + self.IP + self.Port + "/index.shtml"
                        Scrape.URLWithAuthenticate(self.User,self.Password,URL)
                        if Scrape.soup == "":
                                URL = "http://" + self.IP + self.Port + "/Main.shtml"
                                Scrape.URLWithAuthenticate(self.User,self.Password,URL)

                        result ["Type"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sArbVer",Attribute = "value")
                        return result                       

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def ScrapeSetupWebpage(self):
                 
                if self.Error == False:
                
                        
                        #URL = "http://" + self.User + ":" + self.Password + "@" + self.IP + self.Port + "/Main.shtml"
                        URL = "http://" + self.IP + self.Port + "/setup.shtml"
                        result = {}
                        Scrape = lib_WebScraping.WebScraping()
                        Scrape.URLWithAuthenticate(self.User,self.Password,URL)

                        result ["IPAddress"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sArbIP",Attribute = "value")
                        result ["IP_Antenna_A"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAntAIP",Attribute = "value")
                        result ["IP_Antenna_B"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAntBIP",Attribute = "value")
                        result ["Gateway"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sArbGW",Attribute = "value")
                        result ["SubnetMask"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sArbNM",Attribute = "value")
                        result ["TCP_Port"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "uiTCPPort",Attribute = "value")
                        result ["Serial_Baudrate"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "ulArbSerBaud",Attribute = "value")
                        selectionMode =  Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "id", KeyValue = "uiSelectedMode_sel",Attribute = "value")
                        if selectionMode != None:
                                if selectionMode == "1":
                                        selectionMode = "Manual"
                                elif selectionMode == "0":
                                        selectionMode = "AUTO"
                                result ["SwitchSelection"] = selectionMode
                        result ["Telnet_Port"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "uiArbTelnet",Attribute = "value")
                        selectedAntenna =  Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "id", KeyValue = "uiSelectedAnt_sel",Attribute = "value")
                        if selectedAntenna != None:
                                if selectedAntenna == "1":
                                        selectedAntenna = "Antenna_B"
                                elif selectedAntenna == "0":
                                        selectedAntenna = "Antenna_A"
                                result ["RFPath"] = selectedAntenna
                        result ["UDP_Port"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "uiArbUDP",Attribute = "value")
                        Ref10MHz =  Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "id", KeyValue = "ui10MhzRef_sel",Attribute = "value")
                        if Ref10MHz != None:
                                if Ref10MHz == "1":
                                        Ref10MHz = "ON"
                                elif Ref10MHz == "0":
                                        Ref10MHz = "OFF"
                                result ["Ref10MHz"] = Ref10MHz
                        GPSSource =  Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "id", KeyValue = "uiGPSSource_sel",Attribute = "value")
                        if GPSSource != None:
                                if GPSSource == "0":
                                        GPSSource = "Active_Antenna"
                                elif GPSSource == "1":
                                        GPSSource = "Antenna_A"
                                elif GPSSource == "2":
                                        GPSSource = "Antenna_B"
                                elif GPSSource == "3":
                                        GPSSource = "OBM"
                                result ["GPS_Source"] = GPSSource
                        MuteOutputPol =  Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "id", KeyValue = "uiMutePol_sel",Attribute = "value")
                        if MuteOutputPol != None:
                                if MuteOutputPol == "0":
                                        MuteOutputPol = "Low_Voltage_Mute"
                                elif MuteOutputPol == "1":
                                        MuteOutputPol = "High_Voltage_Mute"
                                result ["MuteOutputPol"] = MuteOutputPol
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
                                temp = self.ScrapeMainWebpage()
                                if temp != None:
                                        result.update(temp)
                                temp = self.ScrapeSetupWebpage()
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
                                self.log.printError("ERROR in Retreiving Seatel Mediator Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None
