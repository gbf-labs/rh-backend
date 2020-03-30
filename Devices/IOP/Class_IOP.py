import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time

class IOP(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "IOP"
                self.typeFunctions = {}
                self.typeFunctions["IOP"]    = self.IOP
                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def IOP(self, devNumber):
                import Class_IOP_Iridium

                deviceTypeObject = Class_IOP_Iridium.IOP(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                
                return returnValue