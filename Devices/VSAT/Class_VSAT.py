import Class_Device
import sys
import os
import lib_Log
# import lib_SQLdb
import time

class VSAT(Class_Device.Device):

        def __init__(self, INI,memory=None,Command=None):
                self.deviceDescr = "VSAT"
                self.typeFunctions = {}
                self.typeFunctions["Intellian_V80_IARM"]    = self.Intellian_Vxxx_IARM
                self.typeFunctions["Intellian_V80_E2S"]    = self.Intellian_Vxxx_E2S
                self.typeFunctions["Intellian_V100"]    = self.Intellian_Vxxx_IARM
                self.typeFunctions["Intellian_V100_E2S"]    = self.Intellian_Vxxx_E2S
                self.typeFunctions["Intellian_V110"]    = self.Intellian_Vxxx_IARM
                self.typeFunctions["Intellian_V110_E2S"]    = self.Intellian_Vxxx_E2S
                self.typeFunctions["Sailor_900"]        = self.Sailor_900
                self.typeFunctions["Seatel"]        = self.Seatel

                super(self.__class__, self).__init__(INI,memory = memory,Command = Command)

        def Intellian_Vxxx_IARM(self, devNumber):
                import Class_VSAT_Intellian

                deviceTypeObject = Class_VSAT_Intellian.Vxxx_IARM(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)              
                return returnValue


        def Intellian_Vxxx_E2S(self, devNumber):
                import Class_VSAT_Intellian

                deviceTypeObject = Class_VSAT_Intellian.Vxxx_E2S(self.INI, self.deviceDescr, devNumber)
                returnValue  = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                return returnValue

        def Sailor_900(self, devNumber):
                import Class_VSAT_Sailor

                deviceTypeObject = Class_VSAT_Sailor.Sailor_900(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)
                return returnValue

        def Seatel(self, devNumber):
                import Class_VSAT_Seatel

                deviceTypeObject = Class_VSAT_Seatel.Seatel(self.INI, self.deviceDescr, devNumber)
                returnValue = super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)

                return returnValue

        
