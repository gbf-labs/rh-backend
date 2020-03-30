import Class_ReadConfigINI
import Class_GIT
import types

import sys
import os
import time
import lib_Log
# import lib_SQLdb
import lib_CouchDB

class Initialisation(object):

        def __init__(self):
                """Init Class"""
                self.log = lib_Log.Log(PrintToConsole=True)
                self.Error = False
                self.couch_db = lib_CouchDB.COUCH_DATABASE()

        def Default_Initialisation(self):
                """Do initialisation"""

                #Start Initialisation
                self.log.subTitle ("START Initialisation")

                while True:
                        #Read complete INI Files
                        self.INI = Class_ReadConfigINI.INI()
                        imo = self.INI.getOptionInt("INFO","IMO")
                        if imo == 0 or imo == None:
                                self.log.printWarning("IMO is set to 0 or is not defined, Please Configure INI file with correct info")
                                self.log.printWarning("Restart Initialisation in 10 seconds")
                                time.sleep(10)
                        else:
                                break

                #Create database is not exist (INI read before is required)
                self.Create_Database()

                #Read Git Versions
                # self.GitVersions = self.GetGitInfo()
                
                #Write parameters tables
                self.Create_Parameters()

                result = {}
                result["INI"] = self.INI
                # result["GitVersions"] = self.GitVersions

                return result

        def Create_Parameters(self):
                """Create Parameters"""

                if self.Error == False:
                        self.log.printBoldInfo("Update Parameters Table")                       
                        result = {}
                        #loop over sections in INI-File

                        for section in self.INI.INI:
                                #loop over options OR device numbers in section
                                options = {}
                                for optionOrDevNumber in self.INI.INI[section]:
                                        if isinstance( optionOrDevNumber, int ):
                                                #it's a integer so a device number
                                                devNumber = optionOrDevNumber
                                                
                                                #loop over options
                                                options = {}
                                                for option in self.INI.INI[section][devNumber]:
                                                        if isinstance( self.INI.INI[section][devNumber][option], dict ):
                                                                #multiple options
                                                                for optionID in self.INI.INI[section][devNumber][option]:
                                                                        options[str(option) + str(optionID)] = self.INI.getOption(str(section), devNumber,str(option), optionID)
                                                        else:
                                                                #one option for this device
                                                                options[str(option)] = self.INI.getOption(str(section), devNumber, str(option))
                                                
                                                #prepare ini options
                                                result[str(section) + str(devNumber)] = self.PrepareINIOption(options)
                                        else:
                                                #it's not an integer so a device without a number
                                                option = optionOrDevNumber
                                                if isinstance( self.INI.INI[section][option], dict ):
                                                        #multiple options
                                                        for optionID in self.INI.INI[section][option]:
                                                                options[str(option) + str(optionID)] = self.INI.getOption(str(section),str(option), optionID)
                                                else:
                                                        #one option for this device
                                                        options[str(option)] = self.INI.getOption(str(section),str(option))
                                                
                                                #prepare ini options
                                                result[str(section)] = self.PrepareINIOption(options)
                        #Manually set some Parameters Vallues
                        result["NTWCONF1"] = self.PrepareINIOption( {"TYPE" : "Interfaces" })
                        # result["GIT"] = self.PrepareINIOption( self.GitVersions)
                        paramArray = {}
                        paramArray["PARAMETERS"] = {}
                        paramArray["PARAMETERS"][0] = result
                        paramArray["PARAMETERS"][0]["_ExtractInfo"] = {}
                        paramArray["PARAMETERS"][0]["_ExtractInfo"]["ExtractTime"] = time.time()

                        # sql = lib_SQLdb.Database()
                        print("========================================")
                        print("Class_Initialisation")
                        print("========================================")
                        # sql.WriteArrayData(self.INI,paramArray,uniqueTable = "parameters")
                        self.couch_db.write_default_values(self.INI, paramArray, uniqueTable = "parameters")
                        """
                        #create SQL instance
                        sql = lib_SQLdb.Database()
                        sql.Create_General_Option_Module(self.INI,result,"PARAMETERS",ModuleOption = "Option")
                        import pprint
                        pprint.pprint(paramArray)
                        """
                        return
                else:
                        self.log.printError("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

        def PrepareINIOption(self,RawData):
                """Prepare INI option"""
                if self.Error == False:
                        Data = RawData.copy()
                        try:
                                if "Error" in Data:
                                        if Data["Error"]:
                                                return None
                                        else:
                                                Data.pop("Error",None)
                                for Keys in Data:
                                        Value = Data[Keys]
                                        if type(Value) == bool:
                                                if Value == True :
                                                        Value = "True"
                                                if Value == False :
                                                        Value = "False"
                                                Data[Keys] = Value
                                return Data
                        except:
                                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                                self.Error = True
                                return None

                else:
                        self.log.printError("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

        def Create_Database(self):
                """Create the database on local server"""
                if self.Error == False:
                        try:
                                Host     = self.INI.getOption("DB_LOCAL","HOST")
                                User     = self.INI.getOption("DB_LOCAL","USER")
                                Password = self.INI.getOption("DB_LOCAL","PASSWORD")
                                imo      = self.INI.getOption("INFO","IMO")

                                if None in [Host, User, Password, imo] :
                                        self.log.printError("Host, User, Password or IMO not defined for local database")
                                        self.error=True
                                else:
                                        # DB = "rhbox_%s" % imo
                                        # DB = "rhdev_%s" % imo
                                        # self.log.printBoldInfo("Create Database %s" %DB)
                                        self.log.printBoldInfo("Create Database")
                                        # lib_SQLdb.SQL_Create_Database(Host,User,Password,DB)
                                        self.couch_db.couch_create_databases(imo)
                        except:
                                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                                self.Error = True

        def GetGitInfo (self):
                """ Sync Git """

                if self.Error == False:
                        self.log.printBoldInfo("Get Actual Gitversions")
                        self.log.increaseLevel()
                        GIT = Class_GIT.GIT(self.INI)
                        Version = {}                     
                        Version["PHP_DIR"]= GIT.GITDir["WEB"]
                        Version["PYTHON_DIR"]= GIT.GITDir["PYTHON"]
                        Version["PYTHON_CURRENT_VERSION"] = GIT.Get_Version(Version["PYTHON_DIR"])
                        Version["PHP_CURRENT_VERSION"] = GIT.Get_Version(Version["PHP_DIR"])
                        self.log.printInfo("Gitversions successfully retreived")
                        self.log.decreaseLevel()
                        return Version


        def __del__(self):
                pass
