import Class_SNMP
import sys
import os
import lib_Log
# import lib_SQLdb
import time
# import netsnmp
import Class_Device

# class AlarmPanel(Class_SNMP.SNMP):
class AlarmPanel(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None): 



                self.deviceDescr = "ALARMPANEL"
                self.typeFunctions = {}
                self.typeFunctions["Sailor_6103"]           = self.Sailor_TT6103               

                # super(Class_SNMP.SNMP, self).__init__(INI,Command)
                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Sailor_TT6103(self, devNumber):
                import Class_AlarmPanel_Sailor_TT6103
                
                deviceTypeObject = Class_AlarmPanel_Sailor_TT6103.TT6103(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue                