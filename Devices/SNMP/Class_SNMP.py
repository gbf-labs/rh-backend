
import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time
# import netsnmp
import lib_SNMP

class SNMP(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "INISNMP"
                self.typeFunctions = {}
                self.typeFunctions["INISNMP"]    = self.INISNMP_SNMPV2

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def INISNMP_SNMPV2(self, devNumber):
                import Class_SNMP_INISNMP

                deviceTypeObject = Class_SNMP_INISNMP.SNMPV2(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue

        def GetData(self):                
                result = {}    

                SNMPDevice = lib_SNMP.SNMPv2(self.ipaddr)

                for keyword in self.getDataDict:
                        if isinstance(self.getDataDict[keyword],dict):
                                result[keyword] = {}
                                for option in self.getDataDict[keyword]:
                                        result[keyword][option] = SNMPDevice.readSNMP(self.getDataDict[keyword][option])
                        else:
                                if not "General" in result:
                                        result["General"] = {}
                                result["General"][keyword] = SNMPDevice.readSNMP(self.getDataDict[keyword])
                result = self.GetDataCleanup(result)
                return result
        

        def GetDataCleanup(self, result):
                sqlArray = {}
                sqlArray[self.deviceDescr] = {}
                sqlArray[self.deviceDescr][self.devNumber] = {}
                sqlArray[self.deviceDescr][self.devNumber]["General"] = result
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                sqlArray["ReadError"] = False    
                return sqlArray

        