import Class_VSAT
# import MySQLdb
import warnings
import sys
import os
import time
import paramiko
import socket
from parse import *

import lib_Log
import lib_Parsing
import lib_SSH
import lib_Telnet
import lib_SNMP

from pexpect import pxssh

class Sailor_900(Class_VSAT.VSAT):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()


        def Print_Values(self,result):
                if self.Error == False:
                        for key,value in result.items():
                                print("%s = %s" % (key,value))
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

        def GetData(self):
                """
                        Called from device class
                """
                if self.Error == False:
                        Extra = {}
                        try:
                                result = {}
                                temp = self.SNMPData()
                                if temp != None:
                                        result.update(temp)
                                   
                                temp = self.SNMPBlockages()
                                if temp != None:
                                        result.update(temp)

                                sqlArray = {}
                                sqlArray[self.deviceDescr] = {}
                                sqlArray[self.deviceDescr][self.devNumber] = result
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                                sqlArray["ReadError"] = False   
                                return sqlArray

                        except Exception as e:
                                self.log.printError("ERROR in Retreiving VSAT Data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Extra["ReadError"] = True
                                return Extra
                else:
                        self.log.printWarning("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
                        return None

        def SNMPBlockages(self):
                getDataDict = {
                                    #'BlockingzoneIndex'              : '1.3.6.1.4.1.33721.3.1.15.1.1.1.1',
                                    'BlockingzoneEnabled'              : '1.3.6.1.4.1.33721.3.1.15.1.1.2',  
                                    'BlockingzoneType'              : '1.3.6.1.4.1.33721.3.1.15.1.1.3',  
                                    'BlockingzoneStart'              : '1.3.6.1.4.1.33721.3.1.15.1.1.4',  
                                    'BlockingzoneEnd'              : '1.3.6.1.4.1.33721.3.1.15.1.1.5',  
                                    'BlockingzoneLow'              : '1.3.6.1.4.1.33721.3.1.15.1.1.6',
                                    'BlockingzoneHigh'              : '1.3.6.1.4.1.33721.3.1.15.1.1.6',                                       
                                    }
                #get number of outputs
                snmpDevice = lib_SNMP.SNMPv2(self.INI.getOption(self.deviceDescr, self.devNumber, "IP"))
                #BlockingzoneIndexes = snmpDevice.readSNMP(self.getDataDict['BlockingzoneIndex'])
                result = {}
                for x in range (1,9):
                        try:
                                result["blockzone" + str(x)] = {}
                                enabledList = ["","DISABLE","ENABLE"]
                                zoneList = ["","TxAllowed","TxProhibited"]
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneEnabled'] + "." + str(x))
                                result["blockzone" + str(x)]["Status"] = enabledList[int(temp)]
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneType'] + "." + str(x))
                                result["blockzone" + str(x)]["Type"] = zoneList[int(temp)]
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneStart'] + "." + str(x))
                                result["blockzone" + str(x)]["AzStart"] = "{0:.3f}".format(float(temp)/1000)
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneEnd'] + "." + str(x))
                                result["blockzone" + str(x)]["AzEnd"] = "{0:.3f}".format(float(temp)/1000)
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneLow'] + "." + str(x))
                                result["blockzone" + str(x)]["ElStart"] = "{0:.3f}".format(float(temp)/1000)
                                temp = snmpDevice.readSNMP(getDataDict['BlockingzoneHigh'] + "." + str(x))
                                result["blockzone" + str(x)]["ElEnd"] = "{0:.3f}".format(float(temp)/1000)
                        except:
                                pass
                del snmpDevice
                return result
        def SNMPData(self):
                snmpDevice = lib_SNMP.SNMPv2(self.INI.getOption(self.deviceDescr, self.devNumber, "IP"))
                getDataDict = {
                        'SoftwareVersion' : '1.3.6.1.4.1.33721.3.1.1.4.0',
                        'ACUName' : '1.3.6.1.4.1.33721.3.1.1.3.0',
                        'ACUSerial' : '1.3.6.1.4.1.33721.3.1.1.2.0',
                        'AntennaName' : '1.3.6.1.4.1.33721.3.1.1.13.0',
                        'AntennaSerial' : '1.3.6.1.4.1.33721.3.2.2.1.7000.3.4.0',
                        'SatelliteName' : '1.3.6.1.4.1.33721.3.2.2.1.7090.1.1.0',
                        'SatelliteLongitude' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.2.0',
                        'SatelliteSkew' : '1.3.6.1.4.1.33721.3.2.2.1.7090.1.4.0',
                        'SatelliteRxPol' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.9.0',
                        'SatelliteTxPol' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.10.0',
                        'SatelliteElevationCutOff' : '1.3.6.1.4.1.33721.3.2.2.1.7090.1.5',
                        'Down_Translation' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.4.0',
                        'RxIfFreq' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.11.0',
                        'HuntFrequency' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.5.0',
                        'Up_Translation' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.7.0',
                        'TxIfFreq' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.6.0',
                        'TransmitFrequency' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.8.0',
                        'Heading' : '1.3.6.1.4.1.33721.3.1.3.3.1.4.0',
                        'RelativeAz' : '1.3.6.1.4.1.33721.3.1.14.1.0',
                        'Elevation' : '1.3.6.1.4.1.33721.3.1.14.2.0',
                        'RelativePol' : '1.3.6.1.4.1.33721.3.1.14.3.0',
                        'Latitude' : '1.3.6.1.4.1.33721.3.1.3.1.1.2.0',
                        'Longitude' : '1.3.6.1.4.1.33721.3.1.3.1.1.3.0',
                        'AntennaStatus' : '1.3.6.1.4.1.33721.3.2.2.1.7090.2.1.0',
                        'signalstrength' : '1.3.6.1.4.1.33721.3.2.2.1.7000.4.1.0',
                        }
                result = {}
                result["General"] = {}
                for item in getDataDict:
                        try:
                                result["General"][item] = snmpDevice.readSNMP(getDataDict[item])
                        except:
                                pass
                if "SatelliteLongitude" in result["General"]:
                        result["General"]["SatelliteLongitude"] = "{0:.1f}".format(float(result["General"]["SatelliteLongitude"])/1000)
                if "Heading" in result["General"]:
                        result["General"]["Heading"] = "{0:.1f}".format(float(result["General"]["Heading"])/1000)
                if "RelativeAz" in result["General"]:
                        result["General"]["RelativeAz"] = "{0:.1f}".format(float(result["General"]["RelativeAz"])/1000)               
                if "Elevation" in result["General"]:
                        result["General"]["Elevation"] = "{0:.1f}".format(float(result["General"]["Elevation"])/1000)       
                if "RelativePol" in result["General"]:
                        result["General"]["RelativePol"] = "{0:.1f}".format(float(result["General"]["RelativePol"])/1000)
                if "Latitude" in result["General"]:
                        result["General"]["Latitude"] = "{0:.6f}".format(float(result["General"]["Latitude"])/1000000)
                if "Longitude" in result["General"]:
                        result["General"]["Longitude"] = "{0:.6f}".format(float(result["General"]["Longitude"])/1000000)

                del snmpDevice
                return result



