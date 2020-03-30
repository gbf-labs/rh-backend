import Class_Device
import time
import sys
import os
import lib_Log
# import lib_SQLdb

class Modem(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "MODEM"
                self.typeFunctions = {}
                self.typeFunctions["Evolution_X5"] = self.Idirect_X5
                self.typeFunctions["Evolution_X7"] = self.Idirect_X5

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Idirect_X5(self, devNumber):
                import Class_Modem_Idirect

                deviceTypeObject = Class_Modem_Idirect.X5(self.INI, self.deviceDescr, devNumber)
                return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)