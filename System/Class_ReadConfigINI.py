import ConfigParser
import re
import os
from datetime import datetime
import time
import sys
import os.path
import collections
import lib_Log

class INI(object):
        def __init__(self):

                """Init class"""
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                self.iniFiles = {}
                self.iniList = []
                self.INI = {}
                self.INIcount = 1

                #create Emegrency Failover INI file if not exist
                file = "ini/EMGFAILOVER.INI"
                try:
                    fh = open(file,'r')
                except:
                # if file does not exist, create it
                    fh = open(file,'w')
                fh.close()

                self.AddINI ("SYSTEM.INI")
                self.AddINI ("ini/CONFIG.INI")
                self.AddINI ("ini/COMPLEXCONFIG.INI")
                self.AddINI ("ini/NETWORK.INI")
                self.AddINI ("ini/PORTFORWARDING.INI")
                self.AddINI ("ini/FIREWALL.INI")
                self.AddINI ("ini/EMGFAILOVER.INI")
                self.RemoveNoneINIs()
                self.iniList.sort()

        def AddINI(self,Path):
                self.iniList.append(int(self.INIcount))
                self.iniFiles[self.INIcount] = {}
                self.iniFiles[self.INIcount]["path"]         = Path
                self.iniFiles[self.INIcount]["originalDate"] =  self.Get_TimeStamp(self.iniFiles[self.INIcount])
                self.INIcount += 1

        def RemoveNoneINIs(self):
                #Remove INI link if not exist
                oringinalINIFiles = self.iniFiles.copy() 
                for file in oringinalINIFiles:
                        if "path" in self.iniFiles[file]:
                                if not os.path.exists(self.iniFiles[file]["path"]): 
                                        if self.iniFiles[file]["path"] != "SYSTEM.INI" :
                                            self.log.printWarning("INI-File does not exist: %s !" % self.iniFiles[file]["path"])
                                        self.iniFiles.pop (file,None)
                                        self.iniList.remove(file)
                                        
                        else:
                                self.iniFiles.pop (file,None)       



                                
                self.INI_New = False
                try:
                        self.Read_Files()
                except:
                        self.log.printError("Error occured during reading the INI-files");

        def Get_TimeStamp(self,ConfFile):
                """Get timestamp for a given iniFile"""
                try:
                        mtime = None
                        if "path" in ConfFile:
                                if os.path.exists(ConfFile["path"]): 
                                       mtime = os.path.getmtime(ConfFile["path"])
                except OSError:
                        mtime = None
                        self.log.printError("Error retreiving Time Stamp from %s" % ConfFile["path"])
                        
                returnValue = None
                if mtime is None:
                        returnValue = None
                else:
                        returnValue = datetime.fromtimestamp(mtime)
                return returnValue

        def Check_New (self,ConfFile):
                """Check if iniFile is updated"""

                #get timestamp from INI File
                try:
                        mtime = os.path.getmtime(ConfFile["path"])
                except OSError:
                        mtime = 0
                        self.log.printError("Error retreiving Time Stamp from %s" % ConfFile["path"])

                #get timestamp (now)
                New_Date = datetime.fromtimestamp(mtime)

                if New_Date != ConfFile["originalDate"]:
                        New_Date = datetime.fromtimestamp(mtime)
                        self.log.printError("%s has been modified. Timestamp = %s" % (ConfFile["originalDate"],New_Date))
                        self.INI_New = True
                        return self.INI_New

        def Check_All_New(self):
                """Loop over all ini-Files and check if a file is updated"""

                update = False
                #loop over all ini-files
                for currentIniFile in self.iniFiles:
                        if self.Check_New(self.iniFiles[currentIniFile]):
                                update = True

                return update
                
        def Read_Files(self):
                """
                Loop over all ini-Files and fill self.INI
                For some known options, convert to a specific type
                All sections and options are converterd to upper-case

                Output array:
                        INFO o IMO = 0
                             o MMSI = 0
                              ...
                        VSAT o 1        o IP = 0
                             |          o USER = 0
                             |          o PASS = 0
                             |            ...
                             o 2        o IP = 0
                             |          o USER = 0
                             |          o PASS = 0
                             |            ...
                             o ...
                """

                self.INI = {}

                #loop over all ini-files
                # for currentIniFile in self.iniFiles:
                for currentIniFile in self.iniList:
                        iniParser = ConfigParser.SafeConfigParser()
                        iniParser.read( self.iniFiles[currentIniFile]["path"])

                        #run over ini-sections
                        for section in iniParser.sections():
                                
                                #get trailing number (e.g. 1 in VSAT1)
                                m = re.search(r'\d+$', section)
                                devNumber = int(m.group()) if m else None

                                #if devNumber found, remove it from the section name
                                if devNumber is None:
                                        sectionTemp = section.upper()
                                else:
                                        sectionTemp = section.rstrip(str(devNumber)).upper()

                                #see if section allready exist in INI
                                if sectionTemp not in self.INI:
                                        self.INI[sectionTemp] = {}

                                #see if devnumber allready exist in INI
                                if devNumber is not None:
                                        if devNumber not in self.INI[sectionTemp]:
                                                self.INI[sectionTemp][devNumber] = {}

                                #loop over options
                                for option in iniParser.options(section):                                        
                                        
                                        #get trailing number (e.g. 1 in MAIL1, MAIL2, ...)
                                        n = re.search(r'\d+$', option)
                                        
                                        optionNumber = int(n.group()) if n else None                                        
                                        
                                        #if optionNumber is found, remove it from the option name
                                        if optionNumber is None:
                                                optionTemp = option.upper()
                                        else:
                                                optionTemp = option.rstrip(str(optionNumber)).upper()
                                                
                                       
                                        #optionTemp = option.upper()
                                        value = iniParser.get(section, option)

                                        #===< CONVERT COMMON OPTIONS >===========================================

                                        if ( optionTemp in { "PORT" , "SSHPORT", "TELNETPORT"  } ) :
                                                value = iniParser.getint(section, option)

                                        #if (optionTemp == "IP") :
                                        #       value = iniParser.get(section, option).lower()
                                        #       value = iniParser.getint(section, option)
                                        #       value = iniParser.getboolean(section, option)
                                        #       value = iniParser.getfloot(section, option) getfloat ???

                                        #===< END CONVERT COMMON OPTIONS >=======================================

                                        try:
                                                
                                                if devNumber is None:                                                
                                                        if optionTemp not in self.INI[sectionTemp]:
                                                                self.INI[sectionTemp][optionTemp] = {}
                                                                
                                                        if optionNumber is not None:
                                                                if optionNumber not in self.INI[sectionTemp][optionTemp]:
                                                                        self.INI[sectionTemp][optionTemp][optionNumber] = {}
                                                        
                                                                self.INI[sectionTemp][optionTemp][optionNumber] = value
                                                        else:
                                                                self.INI[sectionTemp][optionTemp] = value
                                                else:
                                                        if optionTemp not in self.INI[sectionTemp][devNumber]:
                                                                self.INI[sectionTemp][devNumber][optionTemp] = {}
                                                                
                                                        if optionNumber is not None:
                                                                if optionNumber not in self.INI[sectionTemp][devNumber][optionTemp]:
                                                                        self.INI[sectionTemp][devNumber][optionTemp][optionNumber] = {}                                        
                                                                
                                                                self.INI[sectionTemp][devNumber][optionTemp][optionNumber] = value
                                                        else:
                                                                self.INI[sectionTemp][devNumber][optionTemp] = value                                        


                                        except:
                                                self.log.printWarning("Skipped option %s in section %s" % (option, section))
                                                pass

        def getOptionStr(self, *childs):
                """
                Get an option out of self.INI
                if option doesn't exist, returns None
                if option exist, convert to string or none
                """
                rawValue = self.getOptionOutOfINI(self.INI, *childs)
                returnValue = None
                if rawValue is not None:
                        try:
                                returnValue = str(rawValue)
                        except:
                                #not possible to convert to int so return None
                                returnValue = None

                return returnValue

        def getOptionInt(self, *childs):
                """
                Get an option out of self.INI
                if option doesn't exist, returns None
                if option exist, convert integer or none
                """
                rawValue = self.getOptionOutOfINI(self.INI, *childs)
                returnValue = None
                if rawValue is not None:
                        try:
                                returnValue = int(rawValue)
                        except:
                                #not possible to convert to int so return None
                                returnValue = None

                return returnValue

        def getOptionBool(self, *childs):
                """
                Get an option out of self.INI
                if option doesn't exist, returns None
                if option exist, convert to true, false or none
                """
                rawValue = self.getOptionStr(*childs)
                returnValue = None

                if rawValue is not None:
                        #false values
                        if rawValue.lower() in ["false","0","off", "no","low"]:
                                returnValue = False

                        #true values
                        if rawValue.lower() in ["true","1","on", "yes","high"]:
                                returnValue = True

                return returnValue

        def getOption(self, *childs):
                """
                Get an option out of self.INI
                if option doesn't exist, returns None
                """
                returnValue = self.getOptionOutOfINI(self.INI, *childs)
                return returnValue

        def getOptionOutOfINI(self, searchList, *childs):
                """
                ONLY USE FUNCTION IN CLASS, see getOption() to use out of class
                Get an option out of a searchList
                Checks if option exists and returns the value,
                if option doesn't exist, returns None
                """
                childs = list(filter(None, childs))

                temp1 = len(childs)
                if temp1 >= 1:
                        needle = childs[0]
                        if needle in searchList.keys():
                                #found in list
                                temp = len(childs)
                                if temp > 2:
                                        returnValue = self.getOptionOutOfINI(searchList[needle], *childs[1:])
                                elif temp == 2:
                                        returnValue = self.getOptionOutOfINI(searchList[needle], childs[1])
                                elif temp == 1:
                                        returnValue = searchList[needle]
                                else:
                                        returnValue = None
                        else:
                                #not found in list
                                returnValue = None
                else:
                        #wrong number of childs
                        returnValue = None

                return returnValue

        def __del__(self):
                pass

        def prettyPrint(self, d, indent=0):
                for key, value in d.items():
                        print('  ' * indent + 'o ' + str(key))
                        if isinstance(value, dict):
                                self.prettyPrint(value, indent+1)
                        else:
                                print('  ' * (indent+1) + ' - ' + str(value))