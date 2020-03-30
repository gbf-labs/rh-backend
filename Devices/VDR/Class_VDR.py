import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time

class VDR(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "VDR"
                self.typeFunctions = {}
                self.typeFunctions["Danalec_VRI1"]    = self.Danalec_VRI1
                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Danalec_VRI1(self, devNumber):
                import Class_VDR_Danalec

                deviceTypeObject = Class_VDR_Danalec.Danalec_VRI1(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject,ModuleOption="ModuleName")
                
                return returnValue