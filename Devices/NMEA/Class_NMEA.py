import Class_Device
import sys
import os
import lib_Log
import time
import lib_Nmea
class NMEA(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "NMEA"
                self.typeFunctions = {}
                self.typeFunctions["ININMEA"]    = self.ININMEA

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def ININMEA(self, devNumber):
                import Class_NMEA_ININMEA
                deviceTypeObject = Class_NMEA_ININMEA.NMEA_0183(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject,ModuleOption="talkerID")              
                return returnValue


        