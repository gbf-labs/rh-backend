import Class_Device
import time
import sys
import os

import lib_Log
# import lib_SQLdb

class NetworkPerformance(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "NTWPERF"
                self.typeFunctions = {}
                self.typeFunctions["PingTest"] = self.PingTest

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def PingTest(self, devNumber):
                import Class_NetworkPerformance_PingTest
                deviceTypeObject = Class_NetworkPerformance_PingTest.PingTest(self.INI, self.deviceDescr, devNumber)
                return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject, ModuleOption="dest")