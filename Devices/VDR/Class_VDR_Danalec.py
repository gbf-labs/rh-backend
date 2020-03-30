import Class_VDR
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

class Danalec_VRI1(Class_VDR.VDR):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()

        
                        
        def ScrapeAlarms(self):
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

                        self.User = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"USER")        
                        if self.User is None:
                                self.User = "vri"


                        self.Password = self.INI.getOptionStr(self.deviceDescr,self.devNumber,"PASSWORD")        
                        if self.Password  is None:
                                self.Password = "vri"

                        URL = "https://" + IP + self.Port + "/vri.php/api/alarm-status?auth-user=" + self.User + "&auth-pwd=" + self.Password

                        result = {}
                        Scrape = lib_WebScraping.WebScraping()
                        #Scrape.URL("http://192.168.40.1/basic_status.ssi")

                        Scrape.URL(URL)

                        result["VesselInfo"] = {}
                        vesselInfo = Scrape.DeepTagSearch(tagList = ["alarm-response","vessel-info"])

                        if vesselInfo:

                                result["VesselInfo"]["VesselName"] = vesselInfo.find("name").string.strip()
                                result["VesselInfo"]["ImoNumber"] = vesselInfo.find("imo-number").string.strip()

                        else:

                                result["VesselInfo"]["VesselName"] = ""
                                result["VesselInfo"]["ImoNumber"] = ""

                        result["AlarmInfo"] = {}
                        activeAlarms = Scrape.DeepTagSearch(tagList = ["alarm-response","alarm-info"])

                        if activeAlarms:

                                result["AlarmInfo"]["CurrentlyActive"] = activeAlarms.find("currently_active").string.strip()
                                result["AlarmInfo"]["OverallInstance"] = activeAlarms.find("overall_instance").string.strip()
                        else:
                                
                                result["AlarmInfo"]["CurrentlyActive"] = ""
                                result["AlarmInfo"]["OverallInstance"] = ""



                        alarmList = Scrape.DeepTagSearch(tagList = ["alarm-response","list"])
                        if alarmList:

                                alarmList = alarmList.find_all('alarm')

                                for word in alarmList:
                                        option = "Alarm_" + str(word["number"]).strip()
                                        result[option] = {}
                                        result[option]["AlarmTimestamp"] = word["timestamp"].strip()
                                        result[option]["AlarmType"] = word["type"].strip()
                                        result[option]["AlarmDescription"] = word.find("text").string.strip()
                        
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
                                temp = self.ScrapeAlarms()
                                if temp != None:
                                        result.update(temp)
                                                                                
                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False    

                                return sqlArray
                                
                        except Exception as e: 
                                self.log.printError("ERROR in Retreiving VDR Data,%s Module Error" % sys._getframe().f_code.co_name) 
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
                self.Disconnect()                
                return False