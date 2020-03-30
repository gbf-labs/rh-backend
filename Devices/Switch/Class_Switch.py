import Class_Device

import sys
import os
import time

import lib_Log
# import lib_SQLdb

class Switch(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "SWITCH"
                self.typeFunctions = {}
                self.typeFunctions["Catalyst_2960"] = self.Catalyst_2960
                self.typeFunctions["Catalyst_3750"] = self.Catalyst_3750
                self.typeFunctions["Cisco_SNMP"] = self.Cisco_SNMP

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Catalyst_2960(self, devNumber):
               import Class_Switch_Cisco

               deviceTypeObject = Class_Switch_Cisco.Catalyst2960(self.INI, self.deviceDescr, devNumber)
               return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject,ModuleOption="port")

        def Catalyst_3750(self, devNumber):
               import Class_Switch_Cisco

               deviceTypeObject = Class_Switch_Cisco.Catalyst3750(self.INI, self.deviceDescr, devNumber)
               return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject,ModuleOption="port")


        def Cisco_SNMP(self, devNumber):
               import Class_Switch_Cisco_SNMP

               deviceTypeObject = Class_Switch_Cisco_SNMP.CiscoSNMP(self.INI, self.deviceDescr, devNumber)
               return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)


