import Class_NetworkPerformance
import sys
import os

import lib_Log
# import lib_SQLdb
import lib_ICMP
import time

class PingTest(Class_NetworkPerformance.NetworkPerformance):

    def __init__(self, INI, deviceDescr, devNumber):
        self.Error = False
        self.log = lib_Log.Log(PrintToConsole=True)
        #for inhiretance from device class
        self.INI = INI
        self.deviceDescr = deviceDescr
        self.devNumber = devNumber
        self.log.increaseLevel()

    def GetData(self):
        if self.Error == False:
            try:
                result = None
                
                pingAdresses = self.INI.getOption(self.deviceDescr, self.devNumber, "IP") 

                if pingAdresses is not None:
                    result = {}
                    for key in pingAdresses:
                        adress = pingAdresses[key].strip()
                        pingTest = lib_ICMP.Ping(adress)
                        result[adress] = pingTest.DoPingTestExtended()
                        
                        if (result[adress]["error"] == True):
                            self.log.printInfo("Ping failed - %s"% adress)
                        else:
                            self.log.printInfo("Ping succesfull - %s"% adress)

                #        sql = lib_SQLdb.Database()
                #Device = "%s%s" % (self.deviceDescr, self.devNumber)
                #sql.Create_General_Option_Module(self.INI,result,Device, ModuleOption="dest")
                sqlArray = {}
                sqlArray[self.deviceDescr] = {}
                sqlArray[self.deviceDescr][self.devNumber] = {}
                sqlArray[self.deviceDescr][self.devNumber]= result
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                sqlArray["ReadError"] = False    
                return sqlArray

            except Exception as e:
                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                self.log.printError( str(e))
                self.Error = True                
                return None