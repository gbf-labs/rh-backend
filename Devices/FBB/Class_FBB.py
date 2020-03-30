import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time

class FBB(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "FBB"
                self.typeFunctions = {}
                self.typeFunctions["Cobham_500"]    = self.FBB_500

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def FBB_500(self, devNumber):
                import Class_FBB_Cobham

                deviceTypeObject = Class_FBB_Cobham.FBB_500(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                return returnValue
                