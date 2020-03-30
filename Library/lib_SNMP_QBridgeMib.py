import lib_SNMP
# import netsnmp
import time
import pprint

import sys
import os
import collections
import binascii
import re
import struct
import lib_Log
import lib_ICMP

#see:
#https://github.com/hardaker/net-snmp/tree/master/python#
#https://github.com/haad/net-snmp/blob/master/python/netsnmp/tests/test.py
#
class QBridgeMibTable(lib_SNMP.SnmpTable):

    def __init__(self):
        self.table = {}
        super(lib_SNMP.SnmpTable, self).__init__()

    """
        PRESETS
    """
    def presetQBrideMib_VlanBased(self):
        self.mainOID = '.1.3.6.1.2.1.17.7.1.4'
        self.subOIDs = {
                        '2.1.3.0':  {'name' : 'dot1qVlanFdbId',                       }, 
                        '2.1.4.0':  {'name' : 'dot1qVlanCurrentEgressPorts',          'convertValueMethod': 'QBridgeMib_PortList', 'interfaceOptionName': 'egressVlans'}, 
                        '2.1.5.0':  {'name' : 'dot1qVlanCurrentUntaggedPorts',        'convertValueMethod': 'QBridgeMib_PortList', 'interfaceOptionName': 'untaggedVlan'}, 
                        '2.1.6.0':  {'name' : 'dot1qVlanStatus',                      'textualConversion': 'QBridgeMib_dot1qVlanStatus'   },                         
                        '3.1.1':    {'name' : 'dot1qVlanStaticName',                  }, 
                        }        

    def getInterfaceVlanInfoTable(self):        
        interfaceTable = {}


        #get all subOids with 'QBridgeMib_PortList' convertValueMethod        
        oidsWithPortList = {}
        for iid, values in self.subOIDs.items():            
            name = values.get('name', None)
            if (isinstance(name, str) and (values.get('convertValueMethod', None) == 'QBridgeMib_PortList')):
                oid = self.mainOID + '.' + iid
                interfaceOptionName = values.get('interfaceOptionName', oid)
                oidsWithPortList.update({oid : {'interfaceOptionName' : interfaceOptionName}})

        
        #loop over all vlans/interfaces        
        for vlanId, values in self.table.items():
            
            #loop over each value with QBridgeMib_PortList conversion
            for oid, oidValues in oidsWithPortList.items():                
                #get snmpObject
                snmpObject = self.table.get(vlanId, {}).get(oid, None)

                #get Raw value
                rawValue = None
                if isinstance(snmpObject, lib_SNMP.SNMPObject):
                    rawValue = snmpObject.convertedValue(None, convertValueMethod = 'raw')
                
                #skip if invalid rawValue
                if rawValue is None:
                    continue                                                
                #get interfaceOptionName
                interfaceOptionName = oidsWithPortList[oid].get('interfaceOptionName', oid)

                #convert rawValue, remove '\x' and remove last 0's                
                numericValues = map(ord, rawValue)

                #figure out portNumbers - input is somting like [0, 0, 0, 0, 0, 0, 255, 192, 0, 0, 0, 255, 240, 0, 0, 0, 0]                                
                for byteCounter in range (0,len(numericValues)): #loop over each byte                    
                    bitCounter = 0
                    for zeroOrOne in '{0:08b}'.format(numericValues[byteCounter]): #loop over each bit (while converting it to 8bit decimal)
                        bitCounter += 1
                        if zeroOrOne == '1':
                            interfaceIndex = str((byteCounter * 8)  + bitCounter)

                            #add interface if not exists
                            if interfaceIndex not in interfaceTable:
                                interfaceTable[interfaceIndex] = {}    
                                                       
                            #add interface option if not exists
                            if interfaceOptionName not in interfaceTable[interfaceIndex]:                                
                                newObject = lib_SNMP.SNMPObject()
                                newObject.forcedOptionName = interfaceOptionName
                                newObject.rawValue = vlanId
                                interfaceTable[interfaceIndex][interfaceOptionName] = newObject
                                del newObject
                            else:
                                oldValue = interfaceTable[interfaceIndex][interfaceOptionName].rawValue
                                newValue = ((oldValue + ', ') if oldValue != '' else '') + vlanId
                                interfaceTable[interfaceIndex][interfaceOptionName].rawValue = newValue
                            

        return interfaceTable
