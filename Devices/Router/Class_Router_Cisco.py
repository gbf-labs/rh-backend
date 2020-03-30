import re
import Class_Router
import fcntl, socket, struct
import telnetlib
import time
import ConfigParser
from datetime import datetime
import warnings
# import MySQLdb
from parse import *
import binascii

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
import lib_SNMP

class Cisco_C8XX(Class_Router.Router):
        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
                self.SetPrompt()

                self.ipaddr = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                self.getDataDict = {
                            'maxIfNumber'           : '1.3.6.1.2.1.2.1.0',
                            'ifDescr'               : '1.3.6.1.2.1.2.2.1.2',
                            'ifPhysAddress'         : '1.3.6.1.2.1.2.2.1.6',#mac adress/interface
                            'ifAdminStatus'         : '1.3.6.1.2.1.2.2.1.7',
                            'ifOperStatus'          : '1.3.6.1.2.1.2.2.1.8',
                            'vlanId'                : '1.3.6.1.4.1.9.9.68.1.2.2.1.2',
                            'vlanStatus'            : '1.3.6.1.4.1.9.9.68.1.2.2.1.3',
                            'vlanMembership'        : '1.3.6.1.4.1.9.9.68.1.2.2.1.1',
                            'serialNumber'          : '1.3.6.1.2.1.47.1.1.1.1.11.1',
                            'modelNumber'           : '1.3.6.1.2.1.47.1.1.1.1.13.1',
                            'softVersion'           : '1.3.6.1.2.1.47.1.1.1.1.10.1',
                            'ifInOctets'           : '1.3.6.1.2.1.2.2.1.10',
                            'ifOutOctets'           : '1.3.6.1.2.1.2.2.1.16',


                            }
                self.ifAdminStatusList = ["","UP","DOWN","TESTING"]
                self.ifOperStatusList = ["","UP","DOWN","Testing","Unknown","Dormant","NotPresent","LowerLayerDown"]
                self.vlanStatusList = ["","Inactive","Active","Shutdown"]
                self.vlanMembershipList = ["","Static","Dynamic","MultiVlan"]

        def SetPrompt(self):
                self.Prompt = [">","#"]

        #def Connect(self,Username = "cisco",Password = "P@55w0rd!", IP = "192.168.199.8",Port = 2323):
        def Connect(self):
                return self.Error
                """
                        Called from modem-class
                        returns True if failed
                """
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
                """
        def Disconnect(self):
                return

                """
                        Called from device-class
                """
                """
                if self.Error == False:
                        self.Telnet.CloseConnection()
                """
        def SetTerminalLength(self):
                """
                        Set Teminal Length
                """
                if self.Error == False:
                        #self.log.printBoldInfo("Configure telnet session")
                        #if next line is deleted, long responses will wait for extra input when console screen is full with text.
                        try:
                                #self.log.printInfo("Waiting for Router...")
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
                                regexCheck = re.compile(r"^(((Fa|Gi)[0-9])|Fa0)")

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

                        returnValue["ExtractTime"] = time.time()
                        return returnValue

        def Version (self):
                if self.Error == False:
                        try:
                                result = {}
                                result[100]= {}
                                temp = self.Telnet.SendCommandWithReturn (ExpectBegin=self.Prompt, Command="show version | include \*1", ExpectEnd=self.Prompt, Timeout=10)
                                temp = temp[:temp.find('\n')]
                                regex = r"(\*1[\s]*)(?P<Type>[\S]*)([\s]*)(?P<Serial>[\S]*)"
                                p=re.compile(regex)
                                m=p.search(temp)                               

                                temp = m.group("Serial") 
                                if temp != None:
                                        result[100]["SerialNumber"] = temp
                                temp = m.group("Type") 
                                if temp != None:
                                        result[100]["ModelNumber"] = temp
                                if result[100] =={}:
                                        return None

                                result[100]["port"] = "General"
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

                        try:
                                result = {}
                                temp = self.getsnmpinfo()
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
                                self.log.printError("ERROR in Retreiving Router data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True                                
                                return Extra

                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

        def getsnmpinfo(self):
                #Run over interfaces
                #get number of interfaces
                snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                returnValue = {}
                number = self.getDataDict['maxIfNumber']
                InterfaceCount = snmpDevice.readSNMP(number,ReadCommunity='public')
                for x in range (1,int(InterfaceCount) + 1):
                        dictionary = {}
                        port = snmpDevice.readSNMP(self.getDataDict['ifDescr'] + "." + str(x)).replace(" ","_")
                        #dictionary["port"] = snmpDevice.readSNMP(self.getDataDict['ifDescr'] + "." + str(x)).replace(" ","_")
                        dictionary["IfMac"] = self.converttomac(snmpDevice.readSNMP(self.getDataDict['ifPhysAddress'] + "." + str(x)))
                        if dictionary["IfMac"] == None:
                                dictionary["IfMac"] = "N/A"
                        temp = snmpDevice.readSNMP(self.getDataDict['ifAdminStatus'] + "." + str(x))
                        dictionary["ifAdminStatus"] = self.ifAdminStatusList[int(temp)]
                        temp = snmpDevice.readSNMP(self.getDataDict['ifOperStatus'] + "." + str(x))
                        dictionary["ifOperStatus"] = self.ifOperStatusList[int(temp)]
                        dictionary["vlan"] = snmpDevice.readSNMP(self.getDataDict['vlanId'] + "." + str(x))
                        if dictionary["vlan"] == None:
                            dictionary["vlan"] = 'N/A'
                        try:
                            temp = snmpDevice.readSNMP(self.getDataDict['vlanStatus'] + "." + str(x))
                            dictionary["vlanStatus"] = self.vlanStatusList[int(temp)]
                        except:
                            dictionary["vlanStatus"] = 'N/A'
                        try:
                            temp = snmpDevice.readSNMP(self.getDataDict['vlanMembership'] + "." + str(x))
                            dictionary["vlanMembership"] = self.vlanMembershipList[int(temp)]
                        except:
                            dictionary["vlanMembership"] = 'N/A'
                        dictionary["ifInOctets"] = snmpDevice.readSNMP(self.getDataDict['ifInOctets'] + "." + str(x))
                        if dictionary["ifInOctets"] == None:
                            dictionary["ifInOctets"] = 'N/A'
                        dictionary["ifOutOctets"] = snmpDevice.readSNMP(self.getDataDict['ifOutOctets'] + "." + str(x))
                        if dictionary["ifOutOctets"] == None:
                            dictionary["ifOutOctets"] = 'N/A'
                        returnValue[port] = dictionary

                        #Get General information
                        returnValue["General"]= {}
                        #get serial
                        returnValue["General"]["SerialNumber"] = snmpDevice.readSNMP(self.getDataDict['serialNumber'])
                        returnValue["General"]["ModelNumber"] = snmpDevice.readSNMP(self.getDataDict['modelNumber'])
                        returnValue["General"]["SoftwareVersion"] = snmpDevice.readSNMP(self.getDataDict['softVersion'])
                return returnValue
        def converttomac(self,mac):
                if mac == None:
                        return None
                try:
                        mac = binascii.hexlify(mac)
                        s = ""
                        for i in range(0,12,2):
                            s += mac[i:i+2] + ":"
                        result=s[:-1]
                        return result
                except:
                        return None