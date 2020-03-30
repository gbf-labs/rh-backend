import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time

class VHF(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "VHF"
                self.typeFunctions = {}
                self.typeFunctions["Sailor_62xx"]    = self.Sailor_62xx

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Sailor_62xx(self, devNumber):
                import Class_VHF_Sailor

                deviceTypeObject = Class_VHF_Sailor.Sailor_62xx(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                return returnValue
                