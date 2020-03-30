import Class_BWTS
import time
import warnings
import sys
import os
import re
import lib_Log
import lib_Modbus

class BioSea_150(Class_BWTS.BWTS):

    def __init__(self, INI, deviceDescr, devNumber):
            self.Error = False
            self.log = lib_Log.Log(PrintToConsole=True)

            #for inhiretance from device class
            self.INI = INI
            self.deviceDescr = deviceDescr
            self.devNumber = devNumber
            self.log.increaseLevel()

            #connection information
            self.IP = None
            self.modBusPort = None
            self.slaveID = None
            self.dictID = 1000

    def Connect(self):
            """
                    Called from device class
                    returns True if failed
            """
            #get vars out of INI
            self.IP = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
            self.modBusPort = self.INI.getOption(self.deviceDescr, self.devNumber, "MODBUSPORT")
            self.slaveID = self.INI.getOption(self.deviceDescr, self.devNumber, "SLAVEID")

            #check ini vars
            if None in (self.IP, self.modBusPort, self.slaveID):
                self.Error = True
                self.log.printError("Error: IP (= %s), ModbusPort (= %s) or SlaveID (= %s) is missing in INI-Files" % (self.IP, self.modBusPort, self.slaveID))
            else:
                #ModBusPort
                if not self.modBusPort.isdigit():
                        self.Error = True
                        self.log.printError("Error: ModbusPort should be numeric (%s given)" % self.modBusPort)
                else:
                        self.modBusPort = int(self.modBusPort)
                #slaveID
                if not self.slaveID.isdigit():
                        self.Error = True
                        self.log.printError("Error: SlaveID should be numeric (%s given)" % self.slaveID)
                else:
                        self.slaveID = int(self.slaveID)

            #connect
            if self.Error == False:
                pass
                try:
                    self.modbusSocket = lib_Modbus.ModBusRTU(self.IP, self.modBusPort, slaveID = [self.slaveID])
                except Exception as e:
                    self.log.printError("ERROR in connecting ModBusRTU - BWTS%s" % self.devNumber)
                    return None

            #return
            return self.Error

    def GetData(self):
            """
                Called from device-class
            """
            if self.Error == False:
                returnValue = {}
                returnValue["ReadError"] = True
                try:
                    self.electricalCabinets = [] #list with available cabinets

                    self.dictID = 1000
                    #general data
                    self.log.printInfo("Get general data")
                    returnValue.update(self.GetGeneralData())
                    #ELC (UVx.x)
                    self.log.printInfo("Get ELC data")
                    returnValue.update(self.GetUVData())
                    #valves
                    self.log.printInfo("Get valve data")
                    returnValue.update(self.GetValveData())
                    #motors
                    self.log.printInfo("Get motor data")
                    returnValue.update(self.GetMotorData())
                    #pumps
                    self.log.printInfo("Get pump data")
                    returnValue.update(self.GetPumpData())
                    #flow measurement
                    self.log.printInfo("Get flow measurement data")
                    returnValue.update(self.GetFlowMeasurementData())
                    #temperature Measurement
                    self.log.printInfo("Get temperature measurement data")
                    returnValue.update(self.GetTemperatureMeasurementData())
                    #UVirradiance measurement
                    self.log.printInfo("Get UV irradiance measurement data")
                    returnValue.update(self.GetUVirradianceMeasurementData())
                    #Get level transmitter data
                    self.log.printInfo("Get level transmitter data")
                    returnValue.update(self.GetLevelTransmitterData())
                    #Thermostats
                    self.log.printInfo("Get thermostats data")
                    returnValue.update(self.GetThermostatData())
                    #Alarms and warnings
                    self.log.printInfo("Get alarms and warnings")
                    returnValue.update(self.GetAlarmsAndWarnings())
                    #Events
                    self.log.printInfo("Get events")
                    returnValue.update(self.GetEvents())

                    #readError
                    returnValue["ReadError"] =False

                    #return
                    return returnValue

                except Exception as e:
                    self.log.printError("ERROR in retreiving BWTS%s data, %s Module Error" % (self.devNumber, sys._getframe().f_code.co_name))
                    self.log.printError(str(e))
                    self.Error = True
                    returnValue["ReadError"] = True
                    return returnValue

            else:
                self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                return None

    def GetUVData(self):
            #init vars
            returnValue = {}
            serialNumberReg = 0x0000 #v2.02.00
            softwareVersReg = 0x00FA #v2.02.00
            currentPowerReg = 0x0064 #v2.02.00
            currentVltgeReg = 0x0082 #v2.02.00
            currentAmpreReg = 0x00A0 #v2.02.00
            powerSetVlueReg = 0x00BE #v2.02.00
            instldLmpPwrReg = 0x00DC #v2.02.00
            lmpOprtngTmeReg = 0x0118 #v2.02.00
            elcStartNmbrReg = 0x0136 #v2.02.00
            defaultNmberReg = 0X0154 #v2.02.00
            uvElcAlarmReg   = 0x0400 #v2.02.00
            orderStatusReg  = 0x0190 #v2.02.00

            defaultStatusBitCounter = 0x01
            defaultStatusResult = 0

            sys.stdout.write('      (* = Skipped)\n')
            sys.stdout.flush()
            sys.stdout.write('      ')
            sys.stdout.flush()

            for major in range(1, 10 + 1): #run from 1-10
                for minor in range(1,2+1): #run from 1-2
                    sys.stdout.write("ELC%s.%s" % (major, minor))
                    sys.stdout.flush()

                    #increase register pointer (but not for first loop)
                    if not (major == 1 and minor == 1):
                        serialNumberReg += 0x02 #v2.02.00
                        softwareVersReg += 0x01 #v2.02.00
                        currentPowerReg += 0x01 #v2.02.00
                        currentVltgeReg += 0x01 #v2.02.00
                        currentAmpreReg += 0x01 #v2.02.00
                        powerSetVlueReg += 0x01 #v2.02.00
                        instldLmpPwrReg += 0x01 #v2.02.00
                        lmpOprtngTmeReg += 0x01 #v2.02.00
                        elcStartNmbrReg += 0x01 #v2.02.00
                        defaultNmberReg += 0X01 #v2.02.00
                        uvElcAlarmReg   += 0x01 #v2.02.00
                        orderStatusReg  += 0x01 #v2.02.00

                        defaultStatusBitCounter += 0x01

                    #get serialNumber
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [(serialNumberReg >> 8), (serialNumberReg & 0xff)])
                    dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                    snYear   = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,6 )['dec']
                    snMonth  = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,7 ,10)['dec']
                    snNumber = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,11,23)['dec']

                    if ((snNumber is None) or (snNumber == 0)):
                        #no serial number found tso do nothing
                        sys.stdout.write("* ")
                        sys.stdout.flush()
                    else:
                        #serial number found, print space
                        sys.stdout.write(" ")
                        sys.stdout.flush()

                        #update available cabinets
                        if (major not in self.electricalCabinets):
                            self.electricalCabinets.append(major)

                        #get firmware
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(softwareVersReg >> 8), (softwareVersReg & 0xff)])
                        result = self.modbusSocket.ExtractData(receivedData)
                        dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                        minorVersion  = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,3 )['dec']
                        majorVersion  = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,4 ,7 )['dec']

                        #current power
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(currentPowerReg >> 8), (currentPowerReg & 0xff)])
                        currentPower = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #current Voltage
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(currentVltgeReg >> 8), (currentVltgeReg & 0xff)])
                        currentVoltage = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #current Amperage
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(currentAmpreReg >> 8), (currentAmpreReg & 0xff)])
                        currentAmperage = float(self.modbusSocket.ExtractData(receivedData)['dataLong']) / 10 #modbus returns in units of 100mA - 12 = 1.2A, so divide by 10

                        #power set value
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(powerSetVlueReg >> 8), (powerSetVlueReg & 0xff)])
                        powerSetValue = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #installed lamp power
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(instldLmpPwrReg >> 8), (instldLmpPwrReg & 0xff)])
                        installedLampPower = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #lamp operating time
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(lmpOprtngTmeReg >> 8), (lmpOprtngTmeReg & 0xff)])
                        lampOperatingTime = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #start number
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(elcStartNmbrReg >> 8), (elcStartNmbrReg & 0xff)])
                        startNumber = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #default number
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(defaultNmberReg >> 8), (defaultNmberReg & 0xff)])
                        defaultNumber = self.modbusSocket.ExtractData(receivedData)['dataLong']

                        #UV/ELC Alarm registers
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [(uvElcAlarmReg   >> 8), (uvElcAlarmReg   & 0xff)])
                        dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                        alarm = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,2 )['dec']  #bit 0 = Discordance PLC/ELC defect
                                                                                                    #bit 1 = Internal defect ELC
                                                                                                    #bit 2 = Defect of lack of safety
                                                                                                    
                        #get order status
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(orderStatusReg >> 8), (orderStatusReg & 0xff)])
                        result = self.modbusSocket.ExtractData(receivedData)
                        dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                        orderStatus  = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,2 )['dec']   #bit 0 = Order of starting ON
                                                                                                            #bit 1 = Order in standby
                                                                                                            #bit 2 = Default

                        #default status bit
                        if (major == 1 and minor == 1):
                                receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x02, 0x08])
                                defaultStatusResult = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                                defaultStatusBitCounter = 0x00

                        if (major == 9 and minor == 1):
                                receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x02, 0x09])
                                defaultStatusResult = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                                defaultStatusBitCounter = 0x00

                        defaultStatusBit = self.modbusSocket.GetPartOfBitArray(defaultStatusResult,defaultStatusBitCounter ,defaultStatusBitCounter )['dec']

                        #build returnValue
                        returnValue[self.dictID] = {}
                        returnValue[self.dictID]["moduleName"] = "UV%s.%s" % (major, minor)
                        returnValue[self.dictID]["snYear"] = snYear
                        returnValue[self.dictID]["snMonth"] = snMonth
                        returnValue[self.dictID]["snNumber"] = snNumber
                        returnValue[self.dictID]["firmware"] = str(majorVersion) + "." + str(minorVersion)
                        returnValue[self.dictID]["currentPower"] = currentPower
                        returnValue[self.dictID]["currentVoltage"] = currentVoltage
                        returnValue[self.dictID]["currentAmperage"] = currentAmperage
                        returnValue[self.dictID]["powerSetValue"] = powerSetValue
                        returnValue[self.dictID]["installedLampPower"] = installedLampPower
                        returnValue[self.dictID]["lampOperatingTime"] = lampOperatingTime
                        returnValue[self.dictID]["startNumber"] = startNumber
                        returnValue[self.dictID]["defaultNumber"] = defaultNumber
                        returnValue[self.dictID]["uvElcAlarm"] = alarm
                        returnValue[self.dictID]["uvStatus"] = orderStatus
                        returnValue[self.dictID]["defaultStatusBit"] = defaultStatusBit
                        self.dictID += 1

            sys.stdout.write("\n")
            sys.stdout.flush()

            #return
            return returnValue

    def GetGeneralData(self):
            #init vars
            returnValue = {}
            returnValue[1] = {} #choose 1 for general, is not needed but makes it easier to remember
            returnValue[1]["moduleName"] = "General"

            #v2.02.00 - get mode status 1
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x05, 0x00])
            result = self.modbusSocket.ExtractData(receivedData)
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(result['dataLong'])
            modeStatus1 = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,16 )['dec']

            #v2.02.00 - get mode status 2
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x05, 0x46])
            result = self.modbusSocket.ExtractData(receivedData)
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(result['dataLong'])
            modeStatus2 = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,16 )['dec']

            modeStatus = modeStatus1 * 1 + modeStatus2 * 256

            #v2.02.00 - volume measurement - m^3
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x00, 0x32])
            volumeMeasurement = self.modbusSocket.ExtractData(receivedData)['dataLong']
            volumeMeasurement = round(lib_Modbus.IEEE_32Bit_to_float(volumeMeasurement),2)

            #v2.02.00 - consumption measurement - kW/h
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x00, 0x46])
            consumption = self.modbusSocket.ExtractData(receivedData)['dataLong']
            consumption = round(lib_Modbus.IEEE_32Bit_to_float(consumption),2)

            #build return value
            returnValue[1]["modeStatus"] = modeStatus
            returnValue[1]["volumeMeasurement"] = volumeMeasurement
            returnValue[1]["consumption"] = consumption

            #returnValue
            return returnValue

    def GetValveData(self):
            #init vars
            returnValue = {}
            number = 0
            alarmReg = 0x00

            #start and end address
            for i in range(0xC2, 0xD4 + 1):
                    number += 1
                    #custom numbers
                    if i == 0xC2: #v2.02.00
                        number = 5
                        alarmReg = 0x047E - 0x01
                    if i == 0xC7: #v2.02.00
                        number = 101
                        alarmReg = 0x0483 - 0x01
                    if i == 0xCE: #v2.02.00
                        number = 201
                        alarmReg = 0x048A - 0x01

                    #get data
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x01, i])
                    result = self.modbusSocket.ExtractData(receivedData)

                    if str(result['dataLong']) is not "0":
                        #alarm
                        alarmReg += 0x01
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(alarmReg   >> 8), (alarmReg   & 0xff)])
                        dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                        alarm = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,1 )['dec']      #bit 0 = Defect opening sensor
                                                                                                        #bit 1 = Defect closing sensor
                        #build returnValue
                        returnValue[self.dictID] = {}
                        returnValue[self.dictID]["valveStatus"] = str(result['dataLong'])
                        returnValue[self.dictID]["valveAlarm"] = alarm
                        returnValue[self.dictID]["moduleName"] = "Y%03d" % number
                        self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetMotorData(self):
            #init vars
            returnValue = {}
            number = 0
            alarmReg = 0x00

            #start and end address
            for i in range(0xD6, 0xDB + 1):
                    number += 1
                    alarmType = "motorAlarmType1"
                    #custom numbers
                    if i == 0xD6: #v2.02.00
                        number = 101
                        alarmReg = 0x044C - 0x01
                    if i == 0xD7: #v2.02.00
                        number = 103
                        alarmReg = 0x044E - 0x01
                    if i == 0xD8: #v2.02.00
                        number = 104
                        alarmReg = 0x044F - 0x01
                    if i == 0xD9: #v2.02.00
                        number = 111
                        alarmReg = 0x0450 - 0x01
                        alarmType = "motorAlarmType2"
                    if i == 0xDA: #v2.02.00
                        number = 102
                        alarmReg = 0x044D - 0x01
                    if i == 0xDB: #v2.02.00
                        number = 211
                        alarmReg = 0x0451 - 0x01
                        alarmType = "motorAlarmType2"

                    #get data
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x01, i])
                    result = self.modbusSocket.ExtractData(receivedData)    #bit 1 = move forward or motor running
                                                                            #bit 2 = default motor (1 way motor)
                                                                            #bit 3 = move backward  (2 way motor)
                                                                            #bit 4 = default motor (2 way motor)
                    
                    #alarm
                    alarmReg += 0x01
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(alarmReg   >> 8), (alarmReg   & 0xff)])
                    dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                    alarm = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,16 )['dec']

                    #build returnValue
                    returnValue[self.dictID] = {}
                    returnValue[self.dictID]["motorStatus"] = str(result['dataLong'])
                    returnValue[self.dictID][alarmType] = alarm
                    returnValue[self.dictID]["moduleName"] = "M%03d" % number
                    self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetPumpData(self):
            #init vars
            returnValue = {}

            number = 0
            #start and end address
            for i in range(0xE0, 0xE2 + 1):
                number += 1
                #custom numbers
                if i == 0xE0: #v2.02.00
                    number = 1
                    alarmReg = 0x04B0
                if i == 0xE1: #v2.02.00
                    number = 101
                    alarmReg = 0x04B1
                if i == 0xE2: #v2.02.00
                    number = 201
                    alarmReg = 0x04B2

                #get data
                receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x01, i])
                result = self.modbusSocket.ExtractData(receivedData)

                #Alarm registers
                receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(alarmReg   >> 8), (alarmReg   & 0xff)])
                dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                alarm = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,16 )['dec'] 

                #build returnValue
                returnValue[self.dictID] = {}
                returnValue[self.dictID]["pumpStatus"] = str(result['dataLong'])
                returnValue[self.dictID]["pumpAlarmType1"] = alarm
                returnValue[self.dictID]["moduleName"] = "P%03d" % number
                self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetFlowMeasurementData(self):
            #init vars
            returnValue = {}

            #flowMeasurement
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x00, 0x36]) #v2.02.00
            result = self.modbusSocket.ExtractData(receivedData)['dataLong']
            result = round(lib_Modbus.IEEE_32Bit_to_float(result),2)

            #v2.02.00 - FT001 - defect sensor or cable break
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x05, 0x32]) #v2.02.00
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
            defect = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,0 )['dec']      #bit 0 = defect thermostat electrical equipment box

            #build returnValue
            returnValue[self.dictID] = {}
            returnValue[self.dictID]["flowMeasurement"] = result
            returnValue[self.dictID]["FMdefect"] = defect
            returnValue[self.dictID]["moduleName"] = "FT001"
            self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetUVirradianceMeasurementData(self):
            #init vars
            returnValue = {}

            #UV irradiance Measurement
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x00, 0x34]) #v2.02.00
            result = self.modbusSocket.ExtractData(receivedData)['dataLong']
            result = round(lib_Modbus.IEEE_32Bit_to_float(result),2)

            #v2.02.00 - UV001 - defect sensor or cable break
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x05, 0x33]) #v2.02.00
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
            defect = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,0 )['dec']      #bit 0 = defect thermostat electrical equipment box

            #build returnValue
            returnValue[self.dictID] = {}
            returnValue[self.dictID]["uvIrradiance"] = result
            returnValue[self.dictID]["UVdefect"] = defect
            returnValue[self.dictID]["moduleName"] = "UV001"
            self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetTemperatureMeasurementData(self):
            #init vars
            returnValue = {}

            #v2.02.00 - temperature measurement - degrees celcius
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x00, 0x38]) #v2.02.00
            result = self.modbusSocket.ExtractData(receivedData)['dataLong']
            result = round(lib_Modbus.IEEE_32Bit_to_float(result),2)

            #v2.02.00 - TT001 - defect sensor or cable break
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x05, 0x30]) #v2.02.00
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
            defect = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,0 )['dec']      #bit 0 = defect thermostat electrical equipment box

            #build returnValue
            returnValue[self.dictID] = {}
            returnValue[self.dictID]["temperature"] = result
            returnValue[self.dictID]["TTdefect"] = defect
            returnValue[self.dictID]["moduleName"] = "TT001"
            self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetThermostatData(self):
            #init vars
            returnValue = {}

            number = 0
            #start and end address
            for i in range(0xC4, 0xCD + 1): #v2.02.00
                    number += 1
                    #custom numbers
                    if i == 0xC4:
                        number = 1

                    #see if cabinet exists in real
                    if number in self.electricalCabinets:
                        #get data
                        receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [0x04, i]) #v2.02.00
                        dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                        defectThermostat = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,0 )['dec']      #bit 0 = defect thermostat electrical equipment box

                        #build returnValue
                        returnValue[self.dictID] = {}
                        returnValue[self.dictID]["TSdefect"] = defectThermostat
                        returnValue[self.dictID]["moduleName"] = "Electrical Cabinet %02d" % number
                        self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetLevelTransmitterData(self):
            #init vars
            returnValue = {}

            #v2.02.00 - LT01 - CIP tank level low
            receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x02], startAddress = [0x05, 0x31]) #v2.02.00
            dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
            defect = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,0 ,0 )['dec']      #bit 0 = defect thermostat electrical equipment box

            #build returnValue
            returnValue[self.dictID] = {}
            returnValue[self.dictID]["LTdefect"] = defect
            returnValue[self.dictID]["moduleName"] = "LT01"
            self.dictID = self.dictID + 1

            #returnValue
            return returnValue

    def GetAlarmsAndWarnings(self):
            #init vars
            returnValue = {}
            returnValue[self.dictID] = {}

            maxBit = 0
            name = ""
            #start and end address
            for i in range(0x0512, 0x0545 + 1):
                    minBit = 0
                    maxBit = 12
                    if i == 0x0512:
                            name = "alarmReg0512"
                    if i == 0x0513:
                            name = "alarmReg0513"
                    if i == 0x0514:
                            name = "alarmReg0514"
                    if i == 0x0515:
                            name = "alarmReg0515"
                    if i == 0x0516:
                            name = "alarmReg0516"
                    if i == 0x0517:
                            name = "alarmReg0517"
                    if i == 0x0518:
                            name = "alarmReg0518"
                    if i > 0x0518 and i < 0x051A: #skip numbers in between
                            continue
                    if i == 0x051A:
                            name = "alarmReg051A"
                    if i > 0x051A and i < 0x051D: #skip numbers in between
                            continue
                    if i == 0x051D:
                            name = "alarmReg051D"
                    if i == 0x051E:
                            name = "alarmReg051E"
                    if i == 0x051F:
                            name = "alarmReg051F"
                    if i == 0x0520:
                            name = "alarmReg0520"
                    if i > 0x0520 and i < 0x0545: #skip numbers in between
                            continue
                    if i == 0x0545:
                            name = "alarmReg0545"

                    #get data
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(i >> 8), (i & 0xff)])
                    dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                    value = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,minBit,maxBit)['dec']      #bit 0 = defect thermostat electrical equipment box

                    #build returnValue
                    returnValue[self.dictID][name] = value

            returnValue[self.dictID]["moduleName"] = "General alarms and warnings"
            self.dictID = self.dictID + 1

            return returnValue

    def GetEvents(self):
            #init vars
            returnValue = {}
            returnValue[self.dictID] = {}

            maxBit = 0
            name = ""
            #start and end address
            for i in range(0x04D8, 0x0546 + 1):
                    minBit = 0
                    maxBit = 0
                    if i == 0x04D8:
                            name = "eventReg04D8"
                    if i == 0x04D9:
                            name = "eventReg04D9"
                    if i == 0x04DA:
                            name = "eventReg04DA"
                    if i == 0x04DB:
                            name = "eventReg04DB"
                    if i > 0x04DB and i < 0x0500: #skip numbers in between
                            continue
                    if i == 0x0500:
                            name = "eventReg0500"
                            maxBit = 5
                    if i == 0x0501:
                            name = "eventReg0501"
                            maxBit = 2
                    if i == 0x0502:
                            name = "eventReg0502"
                    if i == 0x0503:
                            name = "eventReg0503"
                    if i == 0x0504:
                            name = "eventReg0504"
                    if i == 0x0505:
                            name = "eventReg0505"
                    if i > 0x0505 and i < 0x0546: #skip numbers in between
                            continue
                    if i == 0x0546:
                            name = "eventReg0546"
                            maxBit = 10
                    #get data
                    receivedData = self.modbusSocket.SendAndReceive(functionCode = [0x03], requestQuantity = [0x00, 0x01], startAddress = [(i >> 8), (i & 0xff)])
                    dataLongBitArray = self.modbusSocket.ConvertToBitArray(self.modbusSocket.ExtractData(receivedData)['dataLong'])
                    value = self.modbusSocket.GetPartOfBitArray(dataLongBitArray,minBit,maxBit)['dec']      #bit 0 = defect thermostat electrical equipment box

                    #build returnValue
                    returnValue[self.dictID][name] = value

            returnValue[self.dictID]["moduleName"] = "Events"
            self.dictID = self.dictID + 1

            return returnValue