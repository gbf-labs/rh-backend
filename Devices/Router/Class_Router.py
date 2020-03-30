import Class_Device

import sys
import os
import time

import lib_Log
# import lib_SQLdb

class Router(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "ROUTER"
                self.typeFunctions = {}
                self.typeFunctions["Cisco_C8XX"] = self.Cisco_C8XX

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Cisco_C8XX(self, devNumber):
               import Class_Router_Cisco

               deviceTypeObject = Class_Router_Cisco.Cisco_C8XX(self.INI, self.deviceDescr, devNumber)
               return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject,ModuleOption="port")

