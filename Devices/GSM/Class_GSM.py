import Class_Device
import time
import sys
import os
import lib_Log
# import lib_SQLdb

class GSM(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "GSM"
                self.typeFunctions = {}
                self.typeFunctions["PepWave_Max_BR2_AE_IP55"] = self.PepwaveMax

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def PepwaveMax(self, devNumber):
                import Class_GSM_Peplink

                deviceTypeObject = Class_GSM_Peplink.PepwaveMax(self.INI, self.deviceDescr, devNumber)
                return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                
                
           