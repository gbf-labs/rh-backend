#!/usr/bin/python
import re
import Class_Switch
import fcntl, socket, struct
import telnetlib
import time
import ConfigParser
from datetime import datetime
import warnings
# import MySQLdb
from parse import *

#custom-made libraries
import sys
import os
import lib_MAC
import lib_ICMP
import lib_LocalInterface
import lib_Log
# import lib_SQLdb
import lib_Telnet
import lib_Parsing

class Catalyst2960(Class_Switch.Switch):
        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
                self.SetPrompt()

        def SetPrompt(self):
                self.Prompt = [">","#"]

        #def Connect(self,Username = "cisco",Password = "P@55w0rd!", IP = "192.168.199.8",Port = 2323):
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
                        self.Telnet = lib_Telnet.Telnet()
                        if self.Telnet.OpenConnection(ipaddr,port):
                                self.Error = True
                        if self.Error == False:
                                Question = self.Telnet.ReturnQuestion(EndChar = ":").lower()
                                if Question.find("username") >= 0:
                                        self.Telnet.Write(Command = username)
                                        Question = self.Telnet.ReturnQuestion(EndChar = ":").lower()
                                if Question.find("password") >= 0:
                                        self.Telnet.Write(Command = password)
                                self.Telnet.WaitForCursor(ExpectBegin = self.Prompt)
                                self.log.printInfo("Telnet Successfully logged IN")
                return self.Error

        def Disconnect(self):
                """
                        Called from device-class
                """
                if self.Error == False:
                        self.Telnet.CloseConnection()

        def SetTerminalLength(self):
                """
                        Set Teminal Length
                """
                if self.Error == False:
                        #self.log.printBoldInfo("Configure telnet session")
                        #if next line is deleted, long responses will wait for extra input when console screen is full with text.
                        try:
                                #self.log.printInfo("Waiting for switch...")
                                self.Telnet.SendCommandWithoutReturn (Command="term length 0", Prompt=self.Prompt)
                                #self.log.printOK("OK")
                        except:
                                self.log.printError("Ended with errors")
                                self.Error = True

        def UpdateInterfaceStatus(self):
                #UpdateInterfaceStatus
                if self.Error == False: #get command

                        #self.log.printBoldInfo("UpdateInterfaceStatus")
                        result = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show interface status", ExpectEnd=self.Prompt, Timeout=10)


                        interfaceDescriptionIndexList= {}
                        resultDescription = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show interface description", ExpectEnd=self.Prompt, Timeout=10)
                        interfaceDescriptionList = ('interface','status','protocol','description')
                        for line in resultDescription.splitlines():
                                        line = line.lower()
                                        if line.find("interface") >= 0:
                                                for part in interfaceDescriptionList:
                                                        interfaceDescriptionIndexList[part]= {}
                                                        length = len(part)
                                                        x = line.find(part)
                                                        interfaceDescriptionIndexList[part]["begin"] = x
                                                        interfaceDescriptionIndexList[part]["end"] = x + length
                                                break


                        # returnValue = {}
                        # j=0 #set number of lines with mac adress found to 0s
                        try:

                                #get positions of titles
                                interfaceList = ('port','name','status','vlan','duplex','speed','type')
                                interfaceIndexList= {}

                                for line in result.splitlines():
                                        line = line.lower()
                                        if line.find("port") >= 0:
                                                for part in interfaceList:
                                                        interfaceIndexList[part]= {}
                                                        length = len(part)
                                                        x = line.find(part)
                                                        interfaceIndexList[part]["begin"] = x
                                                        interfaceIndexList[part]["end"] = x + length
                                                break
                                regexCheck = re.compile(r"^(((Fa|Gi)[0-9]+\/)|Fa0)")

                                dictionary = {}
                                for line in result.splitlines():
                                        if regexCheck.match(line):
                                                portname = line[interfaceIndexList["port"]["begin"]:interfaceIndexList["name"]["begin"]].strip()
                                                dictionary[portname] = {}
                                                #dict["port"] = line[interfaceIndexList["port"]["begin"]:interfaceIndexList["name"]["begin"]].strip()
                                                # dict["name"] = line[interfaceIndexList["name"]["begin"]:interfaceIndexList["status"]["begin"]].strip()
                                                dictionary[portname]["status"] = line[interfaceIndexList["status"]["begin"]:interfaceIndexList["vlan"]["begin"]].strip()
                                                dictionary[portname]["vlan"] = line[interfaceIndexList["vlan"]["begin"]:interfaceIndexList["duplex"]["begin"]].strip()
                                                dictionary[portname]["duplex"] = line[interfaceIndexList["duplex"]["begin"]:interfaceIndexList["duplex"]["end"]].strip()
                                                dictionary[portname]["speed"] = line[interfaceIndexList["duplex"]["end"]:interfaceIndexList["speed"]["end"]].strip()
                                                dictionary[portname]["type"] = line[interfaceIndexList["speed"]["end"]:].strip()
                                                for line2 in resultDescription.splitlines():
                                                        if regexCheck.match(line2):
                                                                if (portname == line2[interfaceDescriptionIndexList["interface"]["begin"]:interfaceDescriptionIndexList["status"]["begin"]].strip()):
                                                                        dictionary[portname]["name"] = line2[interfaceDescriptionIndexList["description"]["begin"]:].strip()
                                                                        break




                        except Exception as e:
                                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True                                

                        # returnValue["ExtractTime"] = time.time()
                        return dictionary

        def Version (self):
                if self.Error == False:
                        try:
                                result = {}
                                result["General"]= {}
                                temp = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show version | begin Model number", ExpectEnd=self.Prompt, Timeout=10)
                                temp = temp[:temp.find('\n')]
                                temp = lib_Parsing.String_Parse(temp,["Model number"],["ModelNumber"])
                                if temp != None:
                                        result["General"].update(temp)

                                temp = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show version | begin System serial number", ExpectEnd=self.Prompt, Timeout=10)
                                temp = temp[:temp.find('\n')]
                                temp = lib_Parsing.String_Parse(temp,["System serial number"],["SerialNumber"])
                                if temp != None:
                                        result["General"].update(temp)

                                temp = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show version | begin Base ethernet MAC Address", ExpectEnd=self.Prompt, Timeout=10)
                                temp = temp[:temp.find('\n')]
                                temp = lib_Parsing.String_Parse(temp,["Base ethernet MAC Address"],["MacAddress"])
                                if temp != None:
                                        result["General"].update(temp)

                                if result["General"] =={}:
                                        return None

                                result["General"]["port"] = "General"
                                return result
                        except Exception as e:
                                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                return None

        def GetData(self):
                """
                        Called from device-class
                """
                if self.Error == False:
                        Extra = {}
                        self.SetTerminalLength()
                        try:
                                result = {}
                                temp = self.UpdateInterfaceStatus()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Version()
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
                                self.log.printError("ERROR in Retreiving switch data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True                                
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

class Catalyst3750(Catalyst2960):                      
        pass

#class CiscoSwitcha():
#        #constants
#        ERR_TELNETTIMEOUT = "TELNET_TIMEOUT"
#
#        def __init__(self,INIRead,ComplexINIRead):
#                """        function is called when created an instance of this class
#                        Initialize all the variables
#                """
#                self.log = lib_Log.Log(PrintToConsole=True)
#
#                self.INIRead = INIRead
#                self.ComplexINIRead = ComplexINIRead
#                self.DB = ComplexINIRead.Local_Database
#                self.Cisco = INIRead.Temp_Switch
#                #general used variabled
#                self.Errors = False
#                self.ErrorLog = ""
#                self.TelnetReadResult = ""
#                self.telnet = None
#                self.Local_MacAddress = lib_MAC.MAC("0")
#                self.CurrentCiscoPort =""
#
#
#                if self.Cisco.Error == True:
#                        self.Error = True
#
#        def TelnetReadValidation(self,result):
#                "imports tuple in telnet.expect() format, returns true/false"
#                #example: TelnetReadValidation(telnet.expect([r'>', r'#',], Cisco_telnetTimeout))
#                #result[0] the index in the list of the first regular expression that matches
#                        #-1 if timeout
#                        #0 if first item of the list matches
#                        #1 the second item of the list matches
#                #result[1] the match object returned
#                #result[2] the text read up till and including the match.
#                returnValue = True
#                self.TelnetReadResult = result[2]
#                if result[0] == -1:
#                        self.Error = True
#                        self.log.printError("Telnet response timeout")
#                        returnValue = False
#                return returnValue
#
#        def ResetInstance(self):
#                self.__init__()
#
#        def SwitchToEnableMode(self):
#                """send enable command and fill in password, go back to normal mode with SwitchBackToNormalMode()"""
#                if self.Error == False:
#                        try:
#                                self.telnet.write("enable \r\n")
#                                self.log.printInfo("Waiting for switch...")
#                                #wait for password
#                                if not self.TelnetReadValidation(self.telnet.expect([r'assword: '], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                self.telnet.write(self.Cisco.Password + '\r\n')
#                                #wait until in correct mode
#                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)):
#                                        self.Error = True
#                                        self.log.printError("Wrong password entered after enable command ?")
#                                        raise self.ERR_TELNETTIMEOUT
#                        except:
#                                self.Error = True
#
#        def SwitchToConfigureMode(self):
#                """send configure terminal command, go back to Enable mode with SwitchBackToEnableMode()) """
#                if self.Error == False:
#                        try:
#                                self.telnet.write("configure terminal\r\n")
#                                if not self.TelnetReadValidation(self.telnet.expect([r'\(config\)#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)):
#                                        self.Error = True
#                                        self.log.printError("Something went wrong when going into configure mode")
#                                        raise self.ERR_TELNETTIMEOUT
#                        except:
#                                self.Error = True
#
#        def SwitchBackToNormalMode(self):
#                """go back to normal mode (follows on SwitchToEnableMode) """
#                if self.Error == False:
#                        try:
#                                self.telnet.write("disable\r\n")
#                                if not self.TelnetReadValidation(self.telnet.expect([r'>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)):
#                                        self.Error = True
#                                        self.log.printError("Something went wrong when returning back to Normal mode")
#                                        raise self.ERR_TELNETTIMEOUT
#                        except:
#                                self.Error = True
#
#        def SwitchBackToEnableMode(self):
#                """go back to enable mode (follows on SwitchToConfigureModeMode) """
#                if self.Error == False:
#                        try:
#                                self.telnet.write("end\r\n")
#                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)):
#                                        self.Error = True
#                                        self.log.printError("Something went wrong when returning back to enable mode")
#                                        raise self.ERR_TELNETTIMEOUT
#                        except:
#                                self.Error = True
#
#        def FindLocalInterfaceMAC(self):
#                #SHOW MAC
#                if self.Error == False:
#                        self.log.subTitle("Get Local Mac Address")
#                        self.log.printInfo("Interface:  " + self.ComplexINIRead.Switch.Local_interface.interfaceName)
#                        self.Local_MacAddress.address = lib_MAC.MAC.ConvertMACToStandardFormat(self.ComplexINIRead.Switch.Local_interface.getLocalInterfaceHwAddr())
#                        self.log.printInfo("Local MAC:  " + self.Local_MacAddress.GetMACInStandardFormat() + " (" + self.Local_MacAddress.GetMACInCiscoFormat() + ")")
#
#                        prefix = ""
#                        suffix = ""
#                        if self.ComplexINIRead.Switch.ForceMac_Bool:
#                                self.Local_MacAddress.address = self.ComplexINIRead.Switch.ForceMac_Address.address
#                        self.log.printInfo("Forced MAC:  " + self.Local_MacAddress.GetMACInStandardFormat() + " (" + self.Local_MacAddress.GetMACInCiscoFormat() + ") ")
#                        if self.ComplexINIRead.Switch.ForceMac_Bool:
#                                self.log.printWarning("Forced = " + str(self.ComplexINIRead.Switch.ForceMac_Bool))
#                        else:
#                                self.log.printInfo("Forced = " + str(self.ComplexINIRead.Switch.ForceMac_Bool))
#                        if self.Error == False:
#                                self.log.printOK("OK")
#
#        def DoPingTest(self):
#                #DO PING TEST TO CHECK CONNECTION TO SWITCH
#                if self.Error == False:
#                        if not self.ComplexINIRead.Switch.Ping_DoPingTest:
#                                self.log.subTitle("SKIPPED Ping-test to " + self.Cisco.IP, Warning = True)
#                        else:
#                                self.log.subTitle("Ping-test to " + self.Cisco.IP )
#                                if self.Error == False:
#                                        p = lib_ICMP.Ping(self.Cisco.IP)
#                                        i = 0
#                                        j = self.ComplexINIRead.Switch.Ping_RetryMaxNumber
#                                        Ping_Succesfull = False
#                                        if self.ComplexINIRead.Switch.Ping_RetryEnable == False:
#                                                self.log.printWarning("Ping-test retry disabled",0)
#                                                j = 1
#                                        if self.ComplexINIRead.Switch.Ping_RetryMaxNumber == 0:
#                                                j = 1
#
#                                        while i < j:
#                                                i += 1
#                                                if not p.DoPingTest():
#                                                        if self.ComplexINIRead.Switch.Ping_RetryEnable:
#                                                                if self.ComplexINIRead.Switch.Ping_RetryMaxNumber == 0:
#                                                                        self.log.printWarning("Ping test failed (try " + str(i) + " of -forever-)")
#                                                                else:
#                                                                        self.log.printWarning("Ping test failed (try " + str(i) + " of " + str(j) + ")")
#                                                        else:
#                                                                pass  #no retry, so error will be shown
#                                                        if self.ComplexINIRead.Switch.Ping_RetryMaxNumber == 0:
#                                                                j = i + 1
#                                                else:
#                                                        i = j
#                                                        Ping_Succesfull = True
#
#                                        if not Ping_Succesfull:
#                                                self.Error = True
#                                                self.log.printError("Not able to ping Switch on IP address: " + self.Cisco.IP)
#                                        else:
#                                                self.log.printOK("Ping Test OK")
#
#        def OpenTelnet(self):
#                """Open telnet connection"""
#                #INITIATE TELNET CONNECTION
#                if self.Error == False:
#                        self.log.subTitle("Open Telnet connection to " + self.Cisco.IP + ":" + str(self.Cisco.Port))
#                        self.log.printInfo("Waiting for switch...")
#                        try:
#                                self.telnet  = telnetlib.Telnet(self.Cisco.IP, self.Cisco.Port, self.ComplexINIRead.Switch.Cisco_telnetTimeout)
#                        except socket.timeout:
#                                self.Error = True
#                                self.log.printError("Not able to open telnet on  " + self.Cisco.IP + ":" + str(self.Cisco.Port))
#                #FILL IN PASSWORD
#                if self.Error == False:
#                        try:
#                                if not self.TelnetReadValidation(self.telnet.expect([r'assword: '], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                self.telnet.write(self.Cisco.Password + '\r')
#                                if not self.TelnetReadValidation(self.telnet.expect([r'>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)):
#                                        self.Error = True
#                                        self.log.printError("Telnet connection closed - Password wrong ?")
#                                        raise self.ERR_TELNETTIMEOUT
#                                else:
#                                        self.log.printOK("Telnet connection OK")
#                        except:
#                                self.log.printError("Telnet Timeout")
#                                self.Error = True
#
#        def SetTerminalLength(self):
#                """SET TERMINAL LENGTH"""
#                if self.Error == False:
#                        self.log.subTitle("Configure telnet session")
#                        #if next line is deleted, long responses will wait for extra input when console screen is full with text.
#                        try:
#                                self.log.printInfo("Waiting for switch...")
#                                self.telnet.write("term length 0"+ "\r\n")
#                                if not self.TelnetReadValidation(self.telnet.expect([r'witch>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                self.log.printOK("OK")
#                        except:
#                                self.Error = True
#
#        def FindInterfaceName(self):
#                #GET INTERFACE NAME ON CISCO
#                if self.Error == False: #get command
#                        self.log.subTitle("Get Interface on switch")
#
#                        self.telnet.write("show mac address-table address " + self.Local_MacAddress.GetMACInStandardFormat() + " | include " + self.Local_MacAddress.GetMACInCiscoFormat() +  " \r\n") #return mac address table lines, only where local mac-address is found)
#                        self.log.printInfo("Waiting for switch...")
#                        try:
#                                if not self.TelnetReadValidation(self.telnet.expect([r'witch>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                #self.log.printInfo("Parsing response")
#                                i=0 #set number of found field to 0
#                                j=0 #set number of lines with mac adress found to 0s
#                                for line in self.TelnetReadResult.splitlines():
#                                        if (self.Local_MacAddress.GetMACInCiscoFormat() in line): #MAC Address found
#                                                i = 0
#                                                j += 1
#                                                for field in line.split(" "):
#                                                        if field != '':
#                                                                if i == 0:
#                                                                        CiscoInt_VLAN = field
#                                                                elif i == 1:
#                                                                        CiscoInt_MAC = field
#                                                                elif i == 2:
#                                                                        CiscoInt_Type = field
#                                                                elif i == 3:
#                                                                        CiscoInt_Port = field
#                                                                        self.CurrentCiscoPort = CiscoInt_Port
#                                                                else:
#                                                                        self.Error = True
#                                                                        self.log.printError("Multiple fields found for cisco-inteface")
#                                                                i = i + 1
#                                if j != 1: #only one line with given mac address should be used
#                                        self.Error = True
#                                        self.log.printError("MAC-address is found on 0 or multiple interfaces")
#
#
#                        except:
#                                self.Error = True
#                        #DISPLAYS INTERFACE SETTINGS
#                        if self.Error == False:
#                                self.log.printBoldInfo("Switch port status:")
#                                self.log.increaseLevel()
#                                self.log.printInfo("VLAN: " + CiscoInt_VLAN)
#                                self.log.printInfo("MAC : " + CiscoInt_MAC)
#                                self.log.printInfo("Type: " + CiscoInt_Type)
#                                self.log.printInfo("Port: " + self.CurrentCiscoPort)
#                                self.log.decreaseLevel()
#                                self.log.printOK("OK")
#
#        def UpdateInterfaceStatus(self):
#                #UpdateInterfaceStatus
#                if self.Error == False: #get command
#                        self.log.subTitle("UpdateInterfaceStatus")
#                        self.telnet.write("show interface status\r\n")
#                        self.log.printInfo("Waiting for switch...")
#
#                        db_table = "Switch"
#
#
#
#
#
#
#
#
#
#                        # Open database connection
#                        try:
#                                db = MySQLdb.connect(self.DB.Host,self.DB.User,self.DB.Password,self.DB.dbName )
#                        except:
#                                self.log.printError("%s Database does not exist" % sys._getframe().f_code.co_name)
#                                self.Error = True
#
#                        if self.Error == False:
#
#                                # prepare a cursor object using cursor() method
#                                cursor = db.cursor()
#                                # prepare a cursor object using cursor() method
#                                #cursor = db.cursor()
#                                # Create table if not exist
#                                with warnings.catch_warnings():
#                                        warnings.simplefilter('ignore')
#                                        sql = """CREATE TABLE IF NOT EXISTS Switch (
#                                        ID INTEGER PRIMARY KEY AUTO_INCREMENT COMMENT 'SyncMax',
#                                        dateTime DATETIME,
#                                        port CHAR(20),
#                                        name CHAR(20),
#                                        status CHAR(20),
#                                        vlan CHAR(20),
#                                        duplex CHAR(20),
#                                        speed CHAR(20),
#                                        type CHAR(20))"""
#                                        cursor.execute(sql)
#                                # disconnect from server
#                                #db.close()
#
#
#
#
#
#
#                        db_sql = []
#
#                        try:
#                                #if not self.TelnetReadValidation(self.telnet.expect([r'witch>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                self.TelnetReadValidation(self.telnet.expect([r'witch>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout))
#                                #timeStamp = "%.20f" % time.time()
#                                #timeStamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
#                                timeStamp = str(datetime.now())
#                                #self.log.printInfo("Parsing response (timeStamp = " + str(timeStamp) + ")")
#
#                                temp = ""
#                                temp2 = ""
#                                i=0 #set number of found field to 0
#                                j=0 #set number of lines with mac adress found to 0s
#                                for line in self.TelnetReadResult.replace("Not Present", "Not_Present").splitlines():
#                                        j += 1
#                                        i = 0
#                                        lineList = line.split(" ")
#                                        lineList = filter(None, lineList) # filter out empty strings
#                                        lineCount = len(lineList)
#                                        dict = {'port' : '', 'name' : '', 'status' : '', 'vlan' : '', 'duplex' : '', 'speed' : '', 'type' : ''}
#                                        if ("Fa0/" in line) or ("Gi0/" in line):
#                                                for field in lineList:
#
#                                                        if i == 0:
#                                                                temp = ""
#                                                                dict['port'] = field
#                                                        elif i >= 0 and i < lineCount - 6: #description (needed when we have a name in the description)
#                                                                if temp == "":
#                                                                        temp = field
#                                                                else:
#                                                                        temp = temp + " " + field
#                                                        elif i == lineCount - 6: #description
#                                                                if temp == "":
#                                                                        temp = field
#                                                                else:
#                                                                        temp = temp + " " + field
#                                                                dict['name'] = temp
#                                                        elif i == lineCount - 5: #status
#                                                                dict['status'] = field
#                                                        elif i == lineCount - 4: #vlan
#                                                                dict['vlan'] = field
#                                                        elif i == lineCount - 3: #Duplex
#                                                                dict['duplex'] = field
#                                                        elif i == lineCount - 2: #Speed
#                                                                dict['speed'] = field
#                                                        elif i == lineCount - 1: #type
#                                                                dict['type'] = field
#                                                        else:
#                                                                pass
#                                                        i += 1
#                                                db_sql.append("INSERT INTO " + db_table + "(`dateTime`, `port`, `name`, `status`, `vlan` , `duplex`, `speed`, `type`) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}', '{7}');".format(timeStamp, dict['port'],dict['name'],dict['status'],dict['vlan'],dict['duplex'],dict['speed'],dict['type']))
#                                                if temp2 == "":
#                                                        temp2 = dict['port']
#                                                else:
#                                                        temp2 += ", " + dict['port']
#
#                        except:
#                                self.Error = True
#                                self.log.printError("Error during updating the interface status")
#
#                        if self.Error == False:
#                                #insert in table
#
#
#                                #database = lib_SQLdb.Database()
#                                for q in db_sql:   #runs query one by one
#
#                                        try:
#                                                # Execute the SQL command
#                                                cursor.execute (q)
#                                                # Commit your changes in the database
#                                                db.commit()
#                                        except:
#                                                self.log.printError("Database Switch write Failure")
#                                                # Rollback in case there is any error
#                                                db.rollback()
#                                # disconnect from server
#                                db.close()
#
#        def RenameCurrentPort(self):
#                """RENAME CURRENT PORT IN SWITCH"""
#                if self.Error == False:
#                        if not self.ComplexINIRead.Switch.Port_UpdateDescription:
#                                self.log.subTitle("SKIPPED updating port description", Warning = True)
#                        else:
#                                self.log.subTitle("Updating port description (port " + self.CurrentCiscoPort + ") to '" + self.ComplexINIRead.Switch.Port_Description + "'")
#                                self.SwitchToEnableMode()
#                                self.SwitchToConfigureMode()
#
#                                if self.Error == False:
#                                        try:
#                                                self.telnet.write("interface " + self.CurrentCiscoPort + "\r\n")
#                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                self.telnet.write("description " + self.ComplexINIRead.Switch.Port_Description + "\r\n")
#                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'],self. Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                        except:
#                                                self.Error = True
#                                                self.log.printError("Something went wrong during renaming the current port")
#
#                                self.SwitchBackToEnableMode()
#                                self.SwitchBackToNormalMode()
#                                if self.Error == False:
#                                        self.log.printOK("OK")
#
#        def ChangeCurrentPortToTrunk(self):
#                #CHANGE CURRENT PORT IN SWITCH TO TRUNK
#                if self.Error == False:
#                        if not self.ComplexINIRead.Switch.Port_ChangeToTrunk:
#                                self.log.subTitle("SKIPPED updating port to Trunk-mode", Warning = True)
#                        else:
#                                self.log.subTitle("Updating port to trunk mode (port " + self.CurrentCiscoPort + ")")
#                                self.SwitchToEnableMode()
#                                self.SwitchToConfigureMode()
#
#                                if self.Error == False:
#                                        try:
#                                                self.log.printInfo("(This can take some time)")
#                                                self.telnet.write("interface " + self.CurrentCiscoPort + "\r\n")
#                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout * 2)): raise self.ERR_TELNETTIMEOUT
#                                                self.telnet.write("switchport mode trunk\r\n")
#                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout * 2)): raise self.ERR_TELNETTIMEOUT
#                                                self.SwitchBackToEnableMode()
#                                                self.SwitchBackToNormalMode()
#                                        except:
#                                                self.Error = True
#                                                self.log.printError("Something went wrong while changing the current port to trunk modes")
#                                if self.Error == False:
#                                        self.log.printOK("OK")
#
#        def ResetInterfaceWithSameDescription(self):
#                """GET INTERFACES WITH SAME DESCRIPTION"""
#                if self.Error == False: #get command
#                        if not self.ComplexINIRead.Switch.Port_ResetPortsWithSameDescription:
#                                self.log.subTitle("SKIPPED Get interfaces with same description on switch", Warning = True)
#                        else:
#                                self.log.subTitle("Get interfaces with same description and change to default config")
#                                self.log.printInfo("Waiting for switch....")
#                                self.telnet.write("show interface status | include " + self.ComplexINIRead.Switch.Port_Description +  " \r\n") #get all interfaces with the same description
#                                try:
#                                        if not self.TelnetReadValidation(self.telnet.expect([r'witch>'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#
#                                        i=0 #set number of lines found to 0
#                                        j=0 #number of fields found
#                                        temp = self.TelnetReadResult
#                                        for line in temp.splitlines():
#                                                if (self.ComplexINIRead.Switch.Port_Description.lower()) in line.lower():  #filter out lines with description
#                                                        if not "show" in line.lower():  #filter out first line
#                                                                i += 1
#                                                                if self.CurrentCiscoPort.lower() in line.lower(): #filter out line with currently connected port
#                                                                        i -= 1
#                                                                        #self.log.printInfo("Current Port: " + line)
#                                                                        pass
#                                                                else:
#                                                                        #self.log.printInfo("Not Current Port: " + line)
#                                                                        j = 0
#                                                                        for field in line.split(" "):
#                                                                                j += 1
#                                                                                if field != '':
#                                                                                        if j == 1: #Field = port
#                                                                                                self.log.printBoldInfo("Port found with same description: " + field)
#                                                                                                self.log.increaseLevel()
#                                                                                                self.SwitchToEnableMode()
#                                                                                                self.SwitchToConfigureMode()
#                                                                                                #configure port
#                                                                                                if self.Error == False:
#                                                                                                        try:
#                                                                                                                #select interface
#                                                                                                                self.telnet.write("interface " + field + "\r\n")
#                                                                                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                                                                                #remove description
#                                                                                                                self.telnet.write("no description\r\n")
#                                                                                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                                                                                self.log.printInfo("Removed port description")
#                                                                                                                #configure to access (not trunk)
#                                                                                                                self.telnet.write("switchport mode access\r\n")
#                                                                                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                                                                                self.log.printInfo("Configured to access mode")
#                                                                                                                #add vlan 1
#                                                                                                                self.telnet.write("switchport access vlan 1\r\n")
#                                                                                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                                                                                self.log.printInfo("Only access to vlan 1")
#                                                                                                                #back to normal level
#                                                                                                                self.SwitchBackToEnableMode()
#                                                                                                                self.SwitchBackToNormalMode()
#                                                                                                                self.log.printInfo("Finishing commands...")
#                                                                                                        except:
#                                                                                                                self.Error = True
#                                                                                                                self.log.printError("Something went wrong while resetten port with the same description")
#                                                                                                self.log.decreaseLevel()
#                                except:
#                                        self.Error = True
#
#                                if self.Error == False:
#                                        self.log.printOK("OK")
#
#        def CopyRunningConfigToStartupConfig(self):
#                """COPY RUNNING CONFIG TO STARTUP CONFIG"""
#                if self.Error == False:
#                        if not self.ComplexINIRead.Switch.Cisco_SaveRunningConfigToStartupConfig:
#                                self.log.subTitle("SKIPPED copying Running config to startup config", Warning = True)
#                        else:
#                                self.log.subTitle("Copying running config to startup config")
#                                if self.Error == False:
#                                        try:
#                                                self.SwitchToEnableMode()
#                                                self.telnet.write("copy running-config startup-config\r\nstartup-config\r\n"); #do not split commands appart
#                                                if not self.TelnetReadValidation(self.telnet.expect([r'#'], self.ComplexINIRead.Switch.Cisco_telnetTimeout)): raise self.ERR_TELNETTIMEOUT
#                                                self.SwitchBackToNormalMode()
#                                        except:
#                                                self.Error = True
#                                                self.log.printError("Something went wrong while copying the running config to the startup config")
#
#                                if self.Error == False:
#                                        self.log.printOK("OK")
#
#        def CloseTelnet(self):
#                self.log.subTitle("Close Connection")
#                try:
#                        self.telnet.write('exit' + '\r')
#                except:
#                        pass
#
#        def ConfigureConnectedPort(self):
#                """Main Entry point"""
#                #Rename the connected port
#
#                self.Error = False
#                self.DoPingTest()
#                self.FindLocalInterfaceMAC()
#                self.OpenTelnet()
#                self.SetTerminalLength()
#                self.FindInterfaceName()
#                self.RenameCurrentPort()
#                self.ChangeCurrentPortToTrunk()
#                self.ResetInterfaceWithSameDescription()
#                self.CopyRunningConfigToStartupConfig()
#                self.CloseTelnet()
#                if self.Error:
#                        self.log.printError("Ended with errors")
#
#        def GetConnectedPort(self):
#                """Main Entry point"""
#                #find the port on switch where I am connected
#                self.Error = False
#                self.DoPingTest()
#                self.FindLocalInterfaceMAC()
#                self.OpenTelnet()
#                self.SetTerminalLength()
#                self.FindInterfaceName()
#                self.CloseTelnet()
#                if self.Error:
#                        self.log.printError("Ended with errors")
#
#                return self.CurrentCiscoPort
#
#        def ShowInterfaceStatus(self):
#                """Main Entry point"""
#
#                self.Error = False
#                self.DoPingTest()
#                #self.FindLocalInterfaceMAC()
#                self.OpenTelnet()
#                self.SetTerminalLength()
#                #self.FindInterfaceName()
#                self.UpdateInterfaceStatus()
#                self.CloseTelnet()
#                if self.Error:
#                        self.log.printError("Ended with errors")
#
#                return self.CurrentCiscoPort                        
