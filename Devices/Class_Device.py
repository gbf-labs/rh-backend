import time
import sys
import os
import lib_Log
# import lib_SQLdb

"""
o=====================o
| Example Child Class |
o=====================o

import Class_Device
import time
import sys
import os
import lib_Log
import lib_SQLdb

class Modem(Class_Device.Device):

    def __init__(self, INI):
        self.deviceDescr = "MODEM"
        self.typeFunctions = {}
        self.typeFunctions["Evolution_X5"] = self.Idirect_X5

        super(self.__class__, self).__init__(INI)

    def Idirect_X5(self, devNumber):
        import Class_Idirect

        deviceTypeObject = Class_Idirect.X5(self.INI, self.deviceDescr, devNumber)
        return  super(self.__class__,self).deviceTypeFunction(devNumber,deviceTypeObject)

o=============o
| End Example |
o=============o
"""

class Device(object):

    def __init__(self,INI, memory=None, Command=None):
        """
            General INI function for all devices
            self.deviceDescr and self.typeFunctions are expected vars from child-class
        """
        self.log = lib_Log.Log(PrintToConsole=True)
        self.Error = False
        self.INI = INI
        self.ReadError = False
        self.Command=Command
        self.mainEntryFunctions = {}
        self.mainEntryFunctions["reboot"]  = self.Reboot
        self.mainEntryFunctions["restart"] = self.Restart
        self.memory = memory
        
        #self.deviceDescr       ==> from other class (e.g. Modem),
        #                               should contain "MODEM", "VSAT", or ...
        #self.typeFunctions     ==> from other class (e.g. Modem)
        #                               should contain dictionary with device type and function
        #                               e.g. : self.typeFunctions["Evolution_X5"] = self.Idirect_X5

        self.log.subTitle("%s Process started" % self.deviceDescr)


        #get all devices out of the ini
        """
            deviceINI has following format:
                    o 1 o IP = 192.168.0.1
                    |   o user = admin
                    |   o pass = admin
                    |   o ...
                    |
                    o 2 o IP = 192.168.0.1
                    |   o user = admin
                    |   o pass = admin
                    |   o ...
                    ...
        """
        devicesINI = self.INI.getOption(self.deviceDescr)
        
        if devicesINI is None:
            self.Error = True

        #check if no errors
        if self.Error == False:
            self.DeviceList = {}
            #loop over all devices
            for devNumber in devicesINI:

                #check if devNumber is really a number
                if isinstance( devNumber, int ):
                    self.Error = False

                    self.log.printBoldInfo("%s%s" % (self.deviceDescr, devNumber))

                    #check device type in INI-File
                    devType = self.INI.getOption(self.deviceDescr, devNumber, "TYPE")


                    if devType is None:
                        self.Error = True
                        break
                    self.log.increaseLevel()
                    #check if type is know
                    if devType in self.typeFunctions:
                        type = {}
                        type["Type"] = devType
                        type["DateTimeStamp"] =time.time()

                        try:
                            self.DeviceList[devNumber] = self.typeFunctions[devType](devNumber)
                            if self.ReadError:
                                del self.DeviceList[devNumber]
                                self.log.printWarning("Removed %s%s instance due to ReadError" % (self.deviceDescr, devNumber))
                                self.ReadError = False
                            else:
                                if (self.Command == None):
                                    #get Data
                                    i = 0
                                    for key in self.DeviceList[devNumber]:
                                        if self.DeviceList[devNumber][key] == None:
                                            i = i +1
                                    if i > 8:
                                        del self.DeviceList[devNumber]
                                        self.log.printWarning("Removed %s%s instance due to to many ReadErrors (%s)" % (self.deviceDescr, devNumber,i))
                                    else:
                                        self.log.printOK("Data %s%s Succesfully processed" % (self.deviceDescr,devNumber))
                                        self.DeviceList[devNumber].update(type)
                                else:
                                    #not None
                                    if (self.DeviceList[devNumber] == False):
                                        self.log.printOK("%s%s succesfully runned command '%s'" % (self.deviceDescr,devNumber, self.Command["Command"]))
                                    else:
                                        self.log.printError("%s%s had error during '%s'" % (self.deviceDescr,devNumber, self.Command["Command"]))

                        except Exception as e:
                            self.log.printError(self.deviceDescr + " %s Module Error" % sys._getframe().f_code.co_name)
                            self.log.printError( str(e))
                            self.Error = True
                    else:
                        self.log.printWarning( "Type '%s' is unkown and has no program, therefore %s%s is rejected" % (devType,self.deviceDescr,devNumber))
                    self.log.decreaseLevel()

    def deviceTypeFunction(self,i,deviceTypeObject,ModuleOption=None):
        """
                General INI function for all devices
                self.deviceDescr and self.typeFunctions are expected vars from child-class

                calls the following functions
                        *.Connect()
                                Should return True if failed, False = OK
                        *.GetData()
                                Should return None or dictionary
                                        if None:
                                                Data is wrong or corrupted
                                        if Dictionary:
                                                Dictionary should contain field "ReadError", if this is True => data is invalid and thrown away
                                                other fields are copied to database
                        *.Disconnect()

                returns:
                        None if failed
                        dictionary with values (without "ReadError" field") if no fail
        """
        
        if self.Error == False:
            try:
                    #connect
                if deviceTypeObject.Connect():
                    del deviceTypeObject
                    self.ReadError = True
                    return None

                if (self.Command == None):
                    #get data
                    result = deviceTypeObject.GetData()
                    #disconnect
                    deviceTypeObject.Disconnect()
                    del deviceTypeObject

                    #check data
                    if result["ReadError"] or result == None:
                        #data is wrong/corrupted
                        self.ReadError = True
                        return None
                    else:
                        #data is valid
                        result.pop("ReadError",None)

                        #create SQL instance
                    #     sql = lib_SQLdb.Database()

                        # #create tables, fill tables
                        # Device = "%s%s" % (self.deviceDescr, i)
                        # sql.Create_General_Option_Module(self.INI,result,Device,ModuleOption)
                        #import pprint
                        #pprint.pprint(result)
                        self.memory.WriteMemory(result)

                        return result
                else:
                    #not none
                    return  deviceTypeObject.DoCmd(self.Command)

            except Exception as e:
                    #in case of error...
                    self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                    self.log.printError( str(e))
                    self.ReadError = True
                    return None

    def Connect(self):
        """
            Called from device-class
            returns True if failed
            Override this function when needed
        """
        return False

    def Disconnect (self):
        """
            Called from device-class
            Override this function when needed
        """
        return

    def GetData(self):
        """
            Called from device-class
            Override this function when needed
        """
        result = {}
        result["ReadError"] = False
        return result

    def DoCmd(self, command = None, returnValue = None):
        """
            Called from device-class
            returns True if failed
            Override function:
                #  def DoCmd(self, command = None, returnValue = None):
                #     if (command == "beamswitch"):
                #         returnValue = self.BeamSwitch()
                #
                #     return super(self.__class__,self).DoCmd(command, returnValue)
        """
        if "Command" in command:
            if (command["Command"] == "reboot"):
                returnValue = self.Reboot()

            if (command["Command"] == "restart"):
                returnValue = self.Restart()

        return returnValue

    def Reboot(self):
        """
            Called from device-class
            returns True if failed
            Override this function when needed
        """
        print("reboot deviceClass")
        return False


    def Restart(self):
        """
            Called from device-class
            returns True if failed
            Override this function when needed
        """
        print("restart deviceClass")
        return False



    def __del__(self):
        pass