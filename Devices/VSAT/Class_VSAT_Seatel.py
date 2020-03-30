import Class_VSAT
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

class Seatel(Class_VSAT.VSAT):

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
                        if (Scrape.soup == "") or  ( "404 Not Found" in str(Scrape.soup)):
                                URL = "http://" + self.IP + self.Port + "/Main.shtml"
                                Scrape.URLWithAuthenticate(self.User,self.Password,URL)

                        result ["ACU"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAcuVer",Attribute = "value")
                        result ["PCU"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sPcuVer",Attribute = "value")
                        DVB = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sDvbVer",Attribute = "value")
                        DVB = DVB.replace(result ["ACU"], "")
                        result ["DVB"] = DVB.replace('>', '')
                        result ["CommIf"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sIntro",Attribute = "value")
                        
                        self.CommIf = result ["CommIf"]

                        return result
                        
                        

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def ScrapeParameters1Webpage(self):
                 
                if self.Error == False:
                
                        
                        #URL = "http://" + self.User + ":" + self.Password + "@" + self.IP + self.Port + "/Main.shtml"
                        URL = "http://" + self.IP + self.Port + "/parameters1.shtml"
                        result = {}
                        Scrape = lib_WebScraping.WebScraping()
                        Scrape.URLWithAuthenticate(self.User,self.Password,URL)
                        
                        #value="  4006 VER 2.45b" name="sPcuVer"
                        # def FindStringInTagWithKey(self,Tag = "",Keyname = "id", KeyValue = "", Attribute = None):
                        result ["Elevation_Trim"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sElTrim",Attribute = "value")
                        result ["Azimuth_Trim"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzTrim",Attribute = "value")
                        result ["Elevaton_Step_Size"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sElStep",Attribute = "value")
                        result ["Azimuth_Step_Size"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzStep",Attribute = "value")
                        result ["AUTO_threshold"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAgcT",Attribute = "value")
                        result ["Sweep_Increment"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sStepD",Attribute = "value")
                        result ["Search_Increment"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSearchI",Attribute = "value")
                        result ["Step_Integral"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sStepI",Attribute = "value")
                        result ["Search_Limit"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSearchL",Attribute = "value")
                        result ["Polang_Type"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sPolT",Attribute = "value")
                        result ["Search_Delay"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSearchD",Attribute = "value")
                        result ["Polang_Offset_24V"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sPolO24",Attribute = "value")
                        result ["System_Type"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSystemT",Attribute = "value")
                        result ["Polang_Scale_24V"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sPolS24",Attribute = "value")
                        return result
                        
                        

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
        def ScrapeParameters2Webpage(self):
                 
                if self.Error == False:
                
                        
                        #URL = "http://" + self.User + ":" + self.Password + "@" + self.IP + self.Port + "/Main.shtml"
                        URL = "http://" + self.IP + self.Port + "/parameters2.shtml"
                        result = {}
                        Scrape = lib_WebScraping.WebScraping()
                        Scrape.URLWithAuthenticate(self.User,self.Password,URL)
                        
                        #value="  4006 VER 2.45b" name="sPcuVer"
                        # def FindStringInTagWithKey(self,Tag = "",Keyname = "id", KeyValue = "", Attribute = None):
                        result ["Satellite"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSat",Attribute = "value")
                        result ["Az_Limit_1"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL1",Attribute = "value")
                        result ["Frequency_MHz"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sMhz",Attribute = "value")
                        result ["Az_Limit_2"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL2",Attribute = "value")
                        result ["Baudrate"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sKhz",Attribute = "value")
                        result ["Az_Limit_3"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL3",Attribute = "value")
                        result ["Az_Limit_4"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL4",Attribute = "value")
                        result ["Az_Limit_5"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL5",Attribute = "value")
                        result ["Az_Limit_6"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAzL6",Attribute = "value")
                        result ["Target_NID"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sNid",Attribute = "value")
                        result ["Tx_Polarity"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sPolTxT",Attribute = "value")
                        result ["El_Limit_12"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sElL12",Attribute = "value")
                        result ["El_Limit_34"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sElL34",Attribute = "value")
                        result ["El_Limit_56"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sElL56",Attribute = "value")
                        return result
                        
                        

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        
        def ScrapeStatusWebpage(self):
                 
                if self.Error == False:

                        URL = "http://" + self.IP + self.Port + "/status.shtml"
                        result = {}
                        Scrape = lib_WebScraping.WebScraping()
                        Scrape.URLWithAuthenticate(self.User,self.Password,URL)
                        
                        
                        #value="  4006 VER 2.45b" name="sPcuVer"
                        # def FindStringInTagWithKey(self,Tag = "",Keyname = "id", KeyValue = "", Attribute = None):
                        
                        result ["Latitude"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sLat",Attribute = "value")
                        result ["LatitudeDirection"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sLatNS",Attribute = "value")
                        result ["AbsoluteAz"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAz",Attribute = "value")
                        result ["Longitude"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sLon",Attribute = "value")
                        result ["LongitudeDirection"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sLonEW",Attribute = "value")
                        result ["Elevation"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sEl",Attribute = "value")
                        result ["Satellite"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSat",Attribute = "value")
                        result ["SatelliteDirection"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sSatEW",Attribute = "value")
                        
                        result ["RelativeAz"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sRelA",Attribute = "value")
                        result ["Local_Hdg"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sHdg",Attribute = "value")
                        result ["Heading"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sHdgR",Attribute = "value")
                        result ["Threshold"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sThrs",Attribute = "value")
                        result ["AGC"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sAgc",Attribute = "value")
                        result ["Remote_AUX"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sRemA",Attribute = "value")
                        result ["Remote_POL"] = Scrape.FindStringInTagWithKey(Tag = "input",Keyname = "name", KeyValue = "sRemP",Attribute = "value")


                        if self.CommIf == "Comm IF Ver 0.71 P":
                                DishScan = Scrape.soup.find("span",string= re.compile("DishScan")).parent.parent.find("img")["src"]
                                DishScan = DishScan.replace(".gif","")
                                result ["DishScan"] = DishScan
                                #Create own Status level with binary information
                                Tracking = Scrape.soup.find("span",string= re.compile("Tracking")).parent.parent.find("img")["src"]
                                Searching = Scrape.soup.find("span",string= re.compile("Searching")).parent.parent.find("img")["src"]
                                Target = Scrape.soup.find("span",string= re.compile("Target")).parent.parent.find("img")["src"]
                                Blocked = Scrape.soup.find("span",string= re.compile("Blocked")).parent.parent.find("img")["src"]
                                Initalizing = Scrape.soup.find("span",string= re.compile("Initalizing")).parent.parent.find("img")["src"]
                                Error = Scrape.soup.find("span",string= re.compile("Error")).parent.parent.find("img")["src"]
                        #for version 1.11
                        else :
                                DishScan = Scrape.soup.find("td",string= re.compile("DishScan")).parent.find("img")["src"]
                                DishScan = DishScan.replace(".gif","")
                                result ["DishScan"] = DishScan
                                #Create own Status level with binary information
                                Tracking = Scrape.soup.find("td",string= re.compile("Tracking")).parent.find("img")["src"]
                                Searching = Scrape.soup.find("td",string= re.compile("Searching")).parent.find("img")["src"]
                                Target = Scrape.soup.find("td",string= re.compile("Target")).parent.find("img")["src"]
                                Blocked = Scrape.soup.find("td",string= re.compile("Blocked")).parent.find("img")["src"]
                                Initalizing = Scrape.soup.find("td",string= re.compile("Initalizing")).parent.find("img")["src"]
                                Error = Scrape.soup.find("td",string= re.compile("Error")).parent.find("img")["src"]

                        Number = 0
                        if Tracking != "clr.gif":
                                Number += 1
                        if Searching != "clr.gif":
                                Number += 2
                        if Target != "clr.gif":
                                Number += 4
                        if Blocked != "clr.gif":
                                Number += 8
                        if Initalizing != "clr.gif":
                                Number += 16
                        if Error != "clr.gif":
                                Number += 32
                        result ["Status"] = Number
                                              
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
                                temp = self.ScrapeParameters1Webpage()
                                if temp != None:
                                        result.update(temp)
                                temp = self.ScrapeParameters2Webpage()
                                if temp != None:
                                        result.update(temp)
                                temp = self.ScrapeStatusWebpage()
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
                                self.log.printError("ERROR in Retreiving Seatel VSAT Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None
