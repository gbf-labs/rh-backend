
import Class_SNMP
import sys
import os
import lib_Log
# import lib_SQLdb
import time
import netsnmp

class PowerSwitch(Class_SNMP.SNMP):

        def __init__(self, INI,memory=None,Command=None):               
                self.deviceDescr = "POWERSWITCH"
                self.typeFunctions = {}
                self.typeFunctions["Sentry3"]           = self.Sentry_Sentry3
                self.typeFunctions["APC_AP7921"]        = self.APC_AP7921
                self.typeFunctions["Raritan_PX2"]        = self.Raritan_PX2

                super(Class_SNMP.SNMP, self).__init__(INI,memory = memory,Command = Command)

        def Sentry_Sentry3(self, devNumber):
                import Class_PowerSwitch_Sentry

                deviceTypeObject = Class_PowerSwitch_Sentry.Sentry3(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue

        def APC_AP7921(self, devNumber):
                import Class_PowerSwitch_APC

                deviceTypeObject = Class_PowerSwitch_APC.AP7921(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue       
        def Raritan_PX2(self, devNumber):
                import Class_PowerSwitch_Raritan

                deviceTypeObject = Class_PowerSwitch_Raritan.PX2(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue    
                         