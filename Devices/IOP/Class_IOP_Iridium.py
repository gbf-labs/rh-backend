import Class_IOP
import time
import warnings
import sys
import os

from parse import *

import lib_Log
import lib_Parsing
import lib_WebScraping
import lib_GPS
from pexpect import pxssh

class IOP(Class_IOP.IOP):

    def __init__(self, INI, deviceDescr, devNumber):
        self.Error = False
        self.log = lib_Log.Log(PrintToConsole=True)
        #for inhiretance from device class
        self.INI = INI
        self.deviceDescr = deviceDescr
        self.devNumber = devNumber
        self.log.increaseLevel()

    def ScrapeWebpage(self):
        if self.Error == False:
            IP = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"IP")
            if IP is None:
                self.log.printWarning("IP for %s%s not set"%(self.deviceDescr,self.devNumber) )
                return

            self.Port = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"HTTPPORT")        
            if self.Port is None:
                self.Port = ""
            else:
                self.Port = ":" + self.Port


            URL = "http://" + IP + self.Port + "/basic_status.ssi"
            result = {}
            Scrape = lib_WebScraping.WebScraping()
            #Scrape.URL("http://192.168.40.1/basic_status.ssi")
            Scrape.URL(URL)
            if Scrape:

                #result ["ACU"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAcuVer",Attribute = "value")
                result ["Status"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledstat", Attribute = "src")
                result ["Status"] = result ["Status"].replace(".gif","").strip()
                
                result ["Signal"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledsig", Attribute = "src")
                result ["Signal"] = result ["Signal"].replace(".gif","").strip()
                
                result ["GPS"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledgps", Attribute = "src")
                result ["GPS"] = result ["GPS"].replace(".gif","").strip()
                
                result ["Data"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "leddata", Attribute = "src")
                result ["Data"] = result ["Data"].replace(".gif","").strip()
                
                result ["Handset1"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledhs1", Attribute = "src")
                result ["Handset1"] = result ["Handset1"].replace(".gif","").strip()
                
                result ["Handset2"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledhs2", Attribute = "src")
                result ["Handset2"] = result ["Handset2"].replace(".gif","").strip()
                
                result ["Handset3"] = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "ledhs3", Attribute = "src")
                result ["Handset3"] = result ["Handset3"].replace(".gif","").strip()
                
                data = Scrape.FindStringInTagWithKey(Tag = "img",Keyname = "id", KeyValue = "sigstr", Attribute = "src")
                if data == "nobars.png":
                        data = 0
                elif data == "onebar.png":
                        data = 1
                elif data == "twobars.png":
                        data = 2
                elif data == "threebars.png":
                        data = 3
                elif data == "fourbars.png":
                        data = 4
                elif data == "fivebars.png":
                        data = 5
                else:
                        data = None
                result ["Signal_Strength"] = data
                
                result ["Bandwidth"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "bw")
                result ["Sim_Inserted"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "siminst")
                result ["Sim_Error"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "simerr")
                result ["GPS_Status"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "gpsstat")
                
                Latitude = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "gpslat")
                Latitude = Latitude.replace(":"," ")
                Latitude = Latitude.split()
                result ["Latitude"] = lib_GPS.dms2dd(Latitude[0],Latitude[1],0,"")
                
                Longitude = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "gpslon")
                Longitude = Longitude.replace(":"," ")
                Longitude = Longitude.split()
                result ["Longitude"] = lib_GPS.dms2dd(Longitude[0],Longitude[1],0,"")
                
                result ["Connected"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "connected")
                result ["Access_Denial_Cause"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "condenial")
                result ["IP_White_List"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "blockeden")
                result ["Voice_Number_1"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "num1")
                result ["Voice_Number_2"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "num2")
                result ["Voice_Number_3"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "num3")
                del Scrape                                

            URL = "http://" + IP + self.Port + "/diagnostics.ssi"
            Scrape = lib_WebScraping.WebScraping()
            Scrape.URL(URL)
            
            if Scrape:

                # result ["IP"] = Scrape.FindStringInTagWithKey(Tag = "td",Keyname = "id", KeyValue = "num3")
                result ["IMEI"] = Scrape.soup.find("th",string ="Equipment ID (IMEI)").parent.find("td").string
                result ["IMSI"] = Scrape.soup.find("th",string ="IMSI").parent.find("td").string
                result ["MAC"] = Scrape.soup.find("th",string ="MAC Address").parent.find("td").string
                result ["IP"] = Scrape.soup.find("th",string ="IP Address").parent.find("td").string
                result ["firmware"] = Scrape.soup.find("th",string ="Firmware Revision").parent.find("td").string
                result ["hardware"] = Scrape.soup.find("th",string ="Hardware Revision").parent.find("td").string
                result ["bootloader"] = Scrape.soup.find("th",string ="Bootloader Revision").parent.find("td").string

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
                temp = self.ScrapeWebpage()
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
                raise
                self.log.printError("ERROR in Retreiving IOP Data,%s Module Error" % sys._getframe().f_code.co_name) 
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
        #self.FBB.SendCommandWithReturn2("reset")
        self.Disconnect()                
        return False