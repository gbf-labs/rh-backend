import socket
import struct
import time
import sys
import binascii
import lib_Socket

def IEEE_32Bit_to_float(numberIn):
        returnValue = None
        try:
                returnValue = float(struct.unpack('f', struct.pack('I', numberIn))[0])
        except:
                returnValue = None

        return returnValue



class ModBusRTU(object):
        def __init__(self, destHost, destPort, **kwargs):
		#init vars
                self.destHost = destHost
                self.destPort = destPort
                self.slaveID  = kwargs.pop('slaveID', [0x01])
                self.functionCode = kwargs.pop('functionCode', None)
                self.requestQuantity = kwargs.pop('requestQuantity', [0x01])
                self.startAddress = kwargs.pop('startAddress', None)

		#return
                return

        def SendAndReceive(self, **kwargs):
		#init vars
                self.functionCode = kwargs.pop('functionCode', None)
                self.requestQuantity = kwargs.pop('requestQuantity', [0x01])
                self.startAddress = kwargs.pop('startAddress', None)
                
                #build send string
                sendString = []
                sendString = sendString + self.slaveID
                sendString = sendString + self.functionCode
                sendString = sendString + self.startAddress
                sendString = sendString + self.requestQuantity
                sendString = sendString + self.CalcCRC16(sendString)

                #convert list to string
                sendString = ''.join(chr(x) for x in sendString)

                #open socket
                sockUDP = lib_Socket.EthernetSocket(sendHost=self.destHost, sendPort=self.destPort)
                returnData = sockUDP.SendAndReceive(sendString)

		#return
                return returnData

        def CalcCRC16(self, data):
		#calculate CRC
                Constant = 0xA001
                CRC = 0xFFFF
                for c in data:				
                        CRC = CRC ^ c
                        x = 1
                        while x <= 8:
                                useconstant = False
                                if (CRC & 0x01) == 1:
                                        useconstant = True
                                CRC = (CRC >> 1) & 0x7FFF
                                if useconstant == True:
                                	CRC = CRC ^ Constant
                                x += 1
                lsb = (CRC >> 8) & 0xFF
                msb = CRC & 0xFF
		#return CRC
                return [msb,lsb]

        def ExtractData(self, data):
                #init vars
                counter = -1
                result = { 'slaveID' : None, 'functionCode' : None, 'numberOfDataBytes' : None, 'data' : None, 'dataLong' : None, 'checkSum' : None }
                lastDataByte = 0

                #loop over all the bytes in the data
                for currentByte in data:
                        counter = counter + 1
                        #slaveID
                        if counter == 0:
                                result['slaveID'] = currentByte
                        #functionCode
                        if counter == 1:
                                result['functionCode'] = currentByte
                        #numberOfDataByes
                        if counter == 2:
                                result['numberOfDataBytes'] = currentByte
                                lastDataByte = counter + 1 + ord(currentByte)
                        #data
                        if counter > 2 and counter < lastDataByte:
                                if result['data'] is None:
                                        result['data'] = [currentByte]
                                        result['dataLong'] = ord(currentByte)
                                else:
                                        result['data'] = result['data'] + [currentByte]
                                        result['dataLong'] = (result['dataLong'] << 8) + ord(currentByte)

                        #checksum
                        if counter > lastDataByte:
                                if result['checkSum'] is None:
                                        result['checkSum'] = [currentByte]
                                else:
                                        result['checkSum'] = result['checkSum'] + [currentByte]
		#return
                return result

        def ConvertToBitArray(self, data):
		#convert data (int) to bit array
                return [1 if digit=='1' else 0 for digit in bin(data)[2:]]  #2 to remove 0b

        def GetPartOfBitArray(self, data, start, stop):  #start stop from left to right
		#init vars
		result = {}
		#get a specific part of a bit array
                data = list(reversed(data))
                result['bin'] = list(reversed(data[start:stop+1]))
                dec = 0
                for bit in result['bin']:			
                        dec = (dec << 1) | bit
                result['dec'] = dec

		#return
                return result

