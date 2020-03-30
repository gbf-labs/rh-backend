import time
import os
import sys

import lib_Log
# import lib_SQLdb
import lib_SSH

class CoreValues(object):

        def __init__(self,INI,memory,CoreInfo):
                self.memory = memory
                self.Error = False
                #setup log File
                self.log = lib_Log.Log(PrintToConsole = True)
                self.log.subTitle ("Update CoreValues")
               
                self.INI = INI
                self.CoreInfo = CoreInfo

                self.UpdateCoreValues()

        def UpdateCoreValues(self):

                try:
                        CoreValues = {}
                        ServerTime = int(self.GetServerTime())
                        LocalTime = int(time.time())
                        TimeDelta = ServerTime - LocalTime
                        
                        CoreValues["Clock"] = {}
                        CoreValues["Clock"]["TimeDelta"] = TimeDelta
                        CoreValues["CoreInfo"] = self.CoreInfo

                        CoreValues["System"] = {}
                        CoreValues["System"]["SerialNumber"] = os.popen('dmidecode -s system-serial-number -q | grep -v "#"').read()
                        CoreValues["System"]["ProductName"] = os.popen('dmidecode -s system-product-name -q | grep -v "#"').read()
                        # self.log.printBoldInfo("Connecting Local MySQL-Server")

                        result = {}
                        result["COREVALUES"] = {}
                        result["COREVALUES"][0] = CoreValues
                        result["COREVALUES"][0]["_ExtractInfo"] = {}
                        result["COREVALUES"][0]["_ExtractInfo"]["ExtractTime"] = time.time()

                        self.memory.WriteMemory(result)

                        """
                        #create SQL instance
                        sql = lib_SQLdb.Database()
                        sql.Create_General_Option_Module(self.INI,CoreValues,"COREVALUES",ModuleOption = "Option",EmbeddedOption = True)
                        """
                        
                except Exception as e:
                        self.log.printError("ERROR in UpdateCoreValues")
                        self.log.printError( str(e))
                        self.Error = True
        # def GetServerTime(self):
        #         if not self.Error:
        #                 #get server credentials
        #                 self.imoNumber = self.INI.getOptionStr("INFO","IMO")
        #                 self.DB_Remote_Host = self.INI.getOptionStr("DB_RHBOX_SERVER","HOST")
        #                 self.DB_Remote_User = self.INI.getOptionStr("DB_RHBOX_SERVER","USER")
        #                 self.DB_Remote_Password = self.INI.getOptionStr("DB_RHBOX_SERVER","PASSWORD")
        #                 self.DB_Remote = lib_SQLdb.Database()

        #                 #check vars
        #                 if None in (self.imoNumber, self.DB_Remote_Host, self.DB_Remote_User, self.DB_Remote_Password):
        #                         self.Error = True
        #                         self.log.printError("User, Host or Password not defined for local or remote SQL-server")
        #                 else:
        #                         #get dbName
        #                         self.dbName = "rhdev_" + self.imoNumber
        #         if not self.Error:
        #                 if not self.DB_Remote.OpenConnection(self.DB_Remote_User, self.DB_Remote_Password, self.DB_Remote_Host, self.dbName):
        #                         result = self.DB_Remote.Execute_AND_Fetchall("SELECT UNIX_TIMESTAMP()")
        #                         result = result[0]["UNIX_TIMESTAMP()"]
        #                 else:
        #                         self.log.printWarning("Failed in receiving ServerTime, Using localtime instead")
        #                         result = time.time()

        #                 self.DB_Remote.CloseConnection()
        #                 return result

        def GetServerTime(self):
                return time.time()
