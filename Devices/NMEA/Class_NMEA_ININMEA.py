import Class_NMEA
import sys
import os
import time

import lib_Nmea
import lib_Socket
import pprint
import copy

import lib_Log
import copy

class NMEA_0183(Class_NMEA.NMEA):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber
                self.log.increaseLevel()

                #Get INI Variables
                self.interface  = self.INI.getOption(self.deviceDescr, self.devNumber, "INTERFACE")
                self.bindHost   = self.INI.getOption(self.deviceDescr, self.devNumber, "RECEIVEIP")
                self.bindPort   = int(self.INI.getOption(self.deviceDescr, self.devNumber, "RECEIVEPORT"))
                self.captureAll = self.INI.getOption(self.deviceDescr, self.devNumber, "CAPTUREALL")
                self.maxTime = self.INI.getOption(self.deviceDescr, self.devNumber, "CAPTURETIME")
                self.maxTime = int(self.maxTime) if (self.maxTime != None) else 4
                Dictionary = self.INI.getOption(self.deviceDescr, self.devNumber)

                self.getDataDict = []
                # a * in dictionary will make sure, loop runs untill timeout
                if self.captureAll:
                        self.getDataDict.extend("*")
                        self.log.printWarning("CaptureAll --> All NMEA data within %s seconds will be captured" % str(self.maxTime))
                #Get All Get_ items form INI file
                else:
                        for Name in Dictionary:
                                if Name.startswith('GET_') and (Dictionary[Name].lower() == "true"):
                                        self.getDataDict.extend([Name[4:]])
        
        def GetData(self):  
                sqlArray = {}
                sqlArray[self.deviceDescr] = {}
                sqlArray[self.deviceDescr][self.devNumber] = {}

                result = {}
                #create a copy of dictionary to work with
                checklist = copy.deepcopy(self.getDataDict)
                #create NMEA SOCKET
                nmeaSocket = lib_Socket.EthernetSocket(bindPort = self.bindPort, bindHost = self.bindHost, interface = self.interface, INI = self.INI, socketType = "UDP")
                #set initial viariable values
                counter = 0   
                data = {}
                timeout = time.time() + self.maxTime
                Stop = False
                Arraydata = {}
                #loop over the datastrings unil timeout or stop
                while time.time() < timeout and Stop == False:
                        receivedData = nmeaSocket.ReadLine()
                        if receivedData != None:


                                Syntax = lib_Nmea.Nmea(receivedData)
                                result = Syntax.parse()
                                # import pprint
                                # pprint.pprint(result)
                                if result != None:
                                        for talkerID in result:
                                                for item in self.getDataDict:
                                                        #if true, Item of getDataDict if found and should be kept
                                                        if item in result[talkerID] or item == "*":
                                                                Arraydata = self.dict_merge(Arraydata,result)
                                                                if item in checklist and item != "*":
                                                                        checklist.remove(item)
                                                                #if cheklist is empty, all data is found and loop can be stoped
                                                                if checklist == []:
                                                                        Stop = True
                #if keys still exist in checklist, give waring that items are not found.
                for misssingData in checklist:
                        if misssingData != "*":
                                self.log.printWarning("NMEA data %s not found" % misssingData)
                #set the ReadError correct to show all data was processed successfull
                data["ReadError"] = False
                # cleanup the NMEASocket
                del nmeaSocket
                #return the data
                # return data


                sqlArray = {}
                sqlArray[self.deviceDescr] = {}
                sqlArray[self.deviceDescr][self.devNumber] = {}
                sqlArray[self.deviceDescr][self.devNumber] = Arraydata
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                sqlArray["ReadError"] = False  
                # import pprint
                # pprint.pprint (sqlArray)  
                return sqlArray
        def dict_merge(self,a, b):
            '''recursively merges dict's. not just simple a['key'] = b['key'], if
            both a and bhave a key who's value is a dict then dict_merge is called
            on both values and the result stored in the returned dictionary.'''
            if not isinstance(b, dict):
                return b
            result = copy.deepcopy(a)
            for k, v in b.iteritems():
                #print("k is %",k)
                if k in result and isinstance(result[k], dict):
                        result[k] = self.dict_merge(result[k], v)
                else:
                    result[k] = copy.deepcopy(v)
            return result