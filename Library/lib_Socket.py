import socket
import struct
import select
import time
import sys
import binascii
import lib_Log
import lib_IP
import Class_NetworkConfig
import lib_config

class EthernetSocket:
        def __init__(self,**kwargs):
                self.log = lib_Log.Log(PrintToConsole=True)
                #init vars
                self.noErrors = True
                self.socket = None

                # CONFIG
                self.config_data = lib_config.CONFIG_DATA()

                #get arguments
                self.INI = kwargs.pop('INI',None)
                self.sendHost = kwargs.pop('sendHost',None)
                self.interface = kwargs.pop('interface', self.config_data.interface)
                self.sendPort = kwargs.pop('sendPort', None)
                self.receiveBuffer = kwargs.pop('receiveBuffer',1024)
                self.bindHost = kwargs.pop('bindHost', '')
                self.bindPort = kwargs.pop('bindPort',self.sendPort)  #default the same as sendPort
                self.timeOut = kwargs.pop('timeOut', 3)
                self.socketType = kwargs.pop('socketType', "UDP")


                #set bindAddress
                self.bindAddress = None
                if self.bindPort is not None:
                        try:
                                self.bindAddress = (self.bindHost, int(self.bindPort))
                        except:
                                self.log.printError("Error during setting socketUDP-bind adress, host = %s, port = %s (should be numeric)" % (self.bindHost, self.bindPort))                            
                                self.noErrors = False
                else:
                        self.noErrors = False

                if self.noErrors:
                        try:
                                if self.socketType == "TCP":
                                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                else: #UDP or Broadcast
                                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                #special treatment for multicast adresses
                                if lib_IP.CheckIfIPIsMulticastAddress(self.bindHost):
                                    network = Class_NetworkConfig.NetworkConfig(self.INI,"none")
                                    network.AddRoute(self.bindHost,"255.255.255.255",self.interface)
                                    self.socket.bind(('',int(self.bindPort)))
                                    group = socket.inet_aton(self.bindHost)
                                    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
                                    self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                                else:
                                    self.socket.bind(self.bindAddress)
                                self.socket.setblocking(0)
                                return 

                        except Exception as e:
                                self.noErrors = False
                                return 


                return 

    #     def SendAndReceive(self, sendData):
    #             #init vars
    #             recvData = None #will be overwritten with the received data
    #             recvAddr = None #will be overwritten with the receiver address and port (tuple)

    #             #send and receive
    #             if self.noErrors:
    #                     try:
    #                             #create bind
    #                             self.socket.bind(self.bindAddress)





    #                             #send data
    #                             self.socket.sendto(sendData, (self.sendHost, self.sendPort))
    #                             #receive
    #                             recvData, recvAddr = self.socket.recvfrom(self.receiveBuffer)
    #                     finally:
				# #close the socket
    #                             self.socket.close()
    #             #return
    #             return recvData, recvAddr
        def SendAndReceive(self, sendData):
                #init vars
                recvData = None #will be overwritten with the received data
                recvAddr = None #will be overwritten with the receiver address and port (tuple)
                #send and receive
                if self.noErrors:
                        try:
                                #send data
                                self.socket.sendto(sendData, (self.sendHost, self.sendPort))
                                #receive
                                recvData = self.ReadLine()
                        except:
                                self.noErrors = False
                        return recvData


        def ReadLine(self):
                #the last digit in the select method is a timeout
                # data, address = self.socket.recvfrom(1024)
                # print data

                result = select.select([self.socket],[],[],self.timeOut)
                if result[0] == []:
                        self.log.printError("Readline Socket timeout occured")
                        return None
                msg = result[0][0].recv(self.receiveBuffer)
                return msg

        def __del__(self):
                self.socket.close()

