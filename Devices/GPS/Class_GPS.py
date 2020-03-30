import Class_Device
import time
import sys
import os
import lib_Log
# import lib_SQLdb

class GPS(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "GPS"
                self.typeFunctions = {}
                self.typeFunctions["GPSDeamon"] = self.GPSDeamon

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def GPSDeamon(self, devNumber):
                import Class_GPSDeamon
                deviceTypeObject = Class_GPSDeamon.GPSDeamon(self.INI, self.deviceDescr, devNumber)
                return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)