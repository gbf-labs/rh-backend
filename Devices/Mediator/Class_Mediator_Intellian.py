import Class_Mediator
# import MySQLdb
import warnings
import sys
import os
import time
import paramiko
import socket
from parse import *
import re

import lib_Log
import lib_Parsing
import lib_SSH
from pexpect import pxssh

class Intellian_M3_TV03(Class_Mediator.Mediator):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()
                
        def Connect(self):
                """
                        Called from device class
                        returns True if failed
                """
                
                #get vars out of INI
                username = self.INI.getOption(self.deviceDescr, self.devNumber, "USER")
                password = self.INI.getOption(self.deviceDescr, self.devNumber, "PASSWORD")
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "SSHPORT")

                #check ini vars
                if None in (username, password, ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: User (= %s), Password (= %s), IP (= %s) and/or Port (= %s) is missing in INI-Files" % (username, password, ipaddr, port))

                #connect
                if self.Error == False:
                        self.SSH = lib_SSH.SSH()
                        self.SSH.SetPrompt(Prompt = ">")
                        if self.SSH.OpenConnection(username,password,ipaddr,port):
                                self.Error = True
                        return self.Error
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                
                        
        def Get_Mediator(self):
                if self.Error == False:
                        temp = {}
                        result = self.SSH.SendCommandWithReturn(Command="show mediator",Method=1)
                        temp1 = lib_Parsing.String_Parse(result,["Type","Product Name","S/W Version","Serial Number"],["Type","DeviceName","Version","SerialNumber"],Section = "Mediator Information")
                        if temp1 != None:
                                temp.update(temp1)

                        temp1 = lib_Parsing.String_Parse(result,["ACU1 Connection","ACU2 Connection","RF Path","Switch Selection"],["ACU1_Connection","ACU2_Connection","RFPath","SwitchSelection"],Section = "Mediator Status")
                        if temp1 != None:
                                temp.update(temp1)

                        temp1 = lib_Parsing.String_Parse(result,["Touch Key Lock"],["TouchKeyLock"],Section = "Mediator Touch Lock Status")
                        if temp1 != None:
                                temp.update(temp1)

                        temp1 = lib_Parsing.String_Parse(result,["Modem Type","Modem PORT","Modem Protocol","GPS Out Sentence","Use TX Mute","Use Modem Lock","TX Mute","Modem Lock","IP Address","Subnet Mask","Gateway","DNS","TCP Modem Port","UDP Modem Port"],["ModemType","ModemPort","ModemProtocol","GPSOutSentence","UseTXMute","UseModemLock","TXMute","ModemLock","IPAddress","SubnetMask","Gateway","DNS","TCPModemPort","UDPModemPort"],Section = "Mediator Modem Information")
                        if temp1 != None:
                                temp.update(temp1)

                        temp1 = lib_Parsing.String_Parse(result,["Switching Threshold"],["SwitchingThreshold"],Section = "Mediator Switching Threshold Information")
                        if temp1 != None:
                                temp.update(temp1)

                        temp1 = lib_Parsing.String_Parse(result,["Heading Device","Boudrate"],["HeadingDevice","Baudrate"],Section = "Heading Information")
                        if temp1 != None:
                                temp.update(temp1)

                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                
        def Get_iARM(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show iARM version",Method=1)
                        result = lib_Parsing.String_Parse(result,["Active File System Version"],["iARM"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Get_Management(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show config mgmt",Method=1)
                        result = lib_Parsing.String_Parse(result,["MGMT IP Address","MGMT Net Mask","MGMT DHCP Start","MGMT DHCP End","MGMT DHCP Lease Time","MAC Address"],["MGMT_IPAddress","MGMT_NetMask","MGMT_DHCPStart","MGMT_DHCPEnd","MGMT_DHCPLeaseTime","MACAddress"])
                        return result
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Get_AntInfo(self):
                if self.Error == False:
                        result = self.SSH.SendCommandWithReturn(Command="show mediator ant_info",Method=1)
                        regex = r"(Antenna)([0-9])(\s*:)"
                        subst = "[\g<1>\g<2>]"
                        result = re.sub(regex, subst, result, 0)
                        temp = {}
                        temp1 = lib_Parsing.String_Parse(result,["Antenna Status","Signal","RX Lock","TX Enable"],["Antenna1_Status","Antenna1_Signal","Antenna1_RXLock","Antenna1_TXEnable"],Section = "Antenna1")
                        if temp1 != None:
                                temp.update(temp1)
                        temp1 = lib_Parsing.String_Parse(result,["Antenna Status","Signal","RX Lock","TX Enable"],["Antenna2_Status","Antenna2_Signal","Antenna2_RXLock","Antenna2_TXEnable"],Section = "Antenna2")
                        if temp1 != None:
                                temp.update(temp1)
                        return temp
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def Disconnect (self):
                """
                        Called from device class
                """
                self.SSH.CloseConnection()
                        
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
                                temp = self.Get_Mediator()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_iARM()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_Management()
                                if temp != None:
                                        result.update(temp)
                                temp = self.Get_AntInfo()
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
                                self.log.printError("ERROR in Retreiving Mediator Data,%s Module Error" % sys._getframe().f_code.co_name) 
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

