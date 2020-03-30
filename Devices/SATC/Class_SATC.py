
import Class_SNMP
import sys
import os
import lib_Log
# import lib_SQLdb
import time
# import netsnmp

class SATC(Class_SNMP.SNMP):

        def __init__(self, INI,memory=None,Command=None):                
                self.deviceDescr = "SATC"
                self.typeFunctions = {}
                self.typeFunctions["Sailor_3027C"]           = self.Sailor_TT3027C                

                super(Class_SNMP.SNMP, self).__init__(INI,memory = memory,Command = Command)

        def Sailor_TT3027C(self, devNumber):
                import Class_SATC_Sailor_TT3027C

                deviceTypeObject = Class_SATC_Sailor_TT3027C.TT3027C(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue                