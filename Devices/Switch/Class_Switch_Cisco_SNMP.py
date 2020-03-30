import pprint 
import Class_Switch
# import MySQLdb
import warnings
import sys
import os
import time
import socket
from parse import *
import re

import lib_Log
import lib_Parsing
import lib_SSH
from pexpect import pxssh

import lib_SNMP
import netsnmp
# import easysnmp
import binascii

class CiscoSNMP(Class_Switch.Switch):

    def __init__(self, INI, deviceDescr, devNumber):
        self.Error = False
        self.log = lib_Log.Log(PrintToConsole=True)
        #for inhiretance from device class
        self.INI = INI
        self.deviceDescr = deviceDescr
        self.devNumber = devNumber                
        self.log.increaseLevel()

        self.ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")
        self.snmpPort = self.INI.getOption(self.deviceDescr, self.devNumber, "SNMPPORT")
        self.snmpPort = 161 if self.snmpPort is None else self.snmpPort
        self.community = self.INI.getOption(self.deviceDescr, self.devNumber, "SNMPCOMMUNITY")
        self.community = 'public' if self.community is None else self.community
        
                    
        #snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)                
        #outletCount = snmpDevice.readSNMP(self.getDataDict['OutletCount'])
        """
        #pprint.pprint(snmpDevice.getWalkMultiple(netsnmp.VarList(netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.1'), netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.2'), netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.3'))))
        
        #pprint.pprint(snmpDevice.getWalk_SNMPv2MIB())
        """  

    def GetData(self):             

        #== INIT ======================================
        self.log.printBoldInfo('Initialize SNMP Object')
        self.log.increaseLevel()
        snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)                                 
        data = {}
        
        self.log.decreaseLevel()
        
        #== SNMPv2 MIB ================================
        self.log.printBoldInfo('SNMPv2')
        self.log.increaseLevel()
        
        self.log.printInfo('Do basic walk (no table)')
        snmpV2Result = snmpDevice.getWalk_SNMPv2MIB()    

        self.log.printInfo('Merge with previous data')       
        snmpDevice.dictMerge(data, {'General' : snmpDevice.getFormattedDictionary(snmpV2Result)})
        self.log.decreaseLevel()
        
        #== ENTITY MIB ================================
        self.log.printBoldInfo('Entity MIB')
        self.log.increaseLevel()
        
        self.log.printInfo('Init table')
        snmpDevice.initTable('entitymib').presetEntityMib()
        
        self.log.printInfo('Get table over SNMP')
        snmpDevice.fillTable('entitymib')
        
        self.log.printInfo('Keep only main entity (highest parent/child)')
        snmpDevice.getTable('entitymib').filterBySnmpObject(
                                                            -1,
                                                            lib_SNMP.SnmpTable.FILTER_KEEP,
                                                            lib_SNMP.SnmpTable.FILTER_BY_RAWVALUE,
                                                            'entPhysicalParentRelPos'
                                                            )
        
        self.log.printInfo('Remove not needed columns')
        snmpDevice.getTable('entitymib').filterByTag(['entPhysicalParentRelPos', 'entPhysicalClass'],  lib_SNMP.SnmpTable.FILTER_REMOVE)
        
        self.log.printInfo('Format result')
        entMib, indexMappingEntMib = snmpDevice.getTable('entitymib').getFormattedDictionary(snmpDevice, None)

        self.log.printInfo('Change to "General"-module')
        entMib['General'] = entMib.pop(entMib.keys()[0])

        self.log.printInfo('Merge with previous data')
        snmpDevice.dictMerge(data, entMib)

        self.log.decreaseLevel()
        
        #== QBRIDGE ===================================
        self.log.printBoldInfo('QBRIDGE-MIB')
        self.log.increaseLevel()
        
        self.log.printInfo('Init table')
        snmpDevice.initQBridgeTable('qbridge').presetQBrideMib_VlanBased()
        
        self.log.printInfo('Get table over SNMP')
        snmpDevice.fillTable('qbridge')

        self.log.printInfo('Get VLAN info per interface')
        interfaceVlanInfoTable = snmpDevice.getTable('qbridge').getInterfaceVlanInfoTable()
        
        #self.log.printInfo('Keep only real interfaces')
        #snmpDevice.getTable('qbridge').filterBySnmpObject(
        #                                                    snmpDevice.textualConversionToValue('ifMib_IANAifType', 'ethernetCsmacd'),
        #                                                    lib_SNMP.SnmpTable.FILTER_KEEP,
        #                                                    lib_SNMP.SnmpTable.FILTER_BY_RAWVALUE,
        #                                                    'ifType'
        #                                                    )
        self.log.printInfo('Remove not needed columns')
        snmpDevice.getTable('qbridge').filterByTag(['dot1qVlanCurrentEgressPorts', 'dot1qVlanCurrentUntaggedPorts'],  lib_SNMP.SnmpTable.FILTER_REMOVE) #remove not-needed columns

        self.log.printInfo('Format result')
        qbridge, indexMapping2 = snmpDevice.getTable('qbridge').getFormattedDictionary(snmpDevice, None, modulePrefix = 'vlan')

        self.log.printInfo('Merge with previous data')
        snmpDevice.dictMerge(data, qbridge)                

        self.log.decreaseLevel()
        
        #== IF MIB ====================================
        self.log.printBoldInfo('IF-MIB')
        self.log.increaseLevel()
        
        self.log.printInfo('Init table')
        snmpDevice.initTable('ifmib').presetIfMib()

        self.log.printInfo('Merge with VLAN Info')
        snmpDevice.getTable('ifmib').table = interfaceVlanInfoTable                
        
        self.log.printInfo('Get table over SNMP')
        snmpDevice.fillTable('ifmib')                
        
        self.log.printInfo('Keep only real interfaces')
        snmpDevice.getTable('ifmib').filterBySnmpObject(
                                                            snmpDevice.textualConversionToValue('ifMib_IANAifType', 'ethernetCsmacd'),
                                                            lib_SNMP.SnmpTable.FILTER_KEEP,
                                                            lib_SNMP.SnmpTable.FILTER_BY_RAWVALUE,
                                                            'ifType'
                                                            )
        self.log.printInfo('Remove not needed columns')
        snmpDevice.getTable('ifmib').filterByTag(['ifType', 'ifSpeed', 'ifIndex'],  lib_SNMP.SnmpTable.FILTER_REMOVE) #remove not-needed columns
        
        self.log.printInfo('Format result, use "ifName" as moduleName')
        ifMib, indexMapping = snmpDevice.getTable('ifmib').getFormattedDictionary(snmpDevice, 'ifName')
        
        self.log.printInfo('Merge with previous data')
        snmpDevice.dictMerge(data, ifMib)

        self.log.decreaseLevel()
        
        #== POWER OVER ETHERNET (Interfaces) ==========
        self.log.printBoldInfo('Power Over Ethernet (interfaces)')
        self.log.increaseLevel()
        
        self.log.printInfo('Init table')
        snmpDevice.initTable('peth').presetPowerEthernetMib()
        
        self.log.printInfo('Get table over SNMP')
        snmpDevice.fillTable('peth')
        
        self.log.printInfo('Checking if index remapping is needed')
        indexMappingRemapped = indexMapping.copy()               
        if not(data.get('General',{}).get('entPhysicalDescr','').find('C2960') == -1):
            self.log.increaseLevel()
            self.log.printInfo('Catalyst 2960 Found, rebuilding index mapping for PoE')
            for index, value in indexMapping.items():
                indexInt = int(index)
                indexLowered = (indexInt - 10000) if (indexInt > 10000) else indexInt
                indexMappingRemapped.update({str(indexLowered) : value})
            self.log.decreaseLevel()

        self.log.printInfo('Format result, use "ifName" as moduleName (re-use indexmapping from IF-MIB)')
        peth, indexMapping2 = snmpDevice.getTable('peth').getFormattedDictionary(snmpDevice, indexMappingRemapped)                
        
        self.log.printInfo('Merge with previous data')
        snmpDevice.dictMerge(data, peth)                
        
        self.log.decreaseLevel()
        
        #== POWER OVER ETHERNET (Group) ===============
        self.log.printBoldInfo('Power Over Ethernet (group)')
        self.log.increaseLevel()
        
        self.log.printInfo('Init table')
        snmpDevice.initTable('pethGrp').presetPowerEthernetGroupMib()
        
        self.log.printInfo('Get table over SNMP')
        snmpDevice.fillTable('pethGrp')

        self.log.printInfo('Format result')
        pethGrp, indexMapping2 = snmpDevice.getTable('pethGrp').getFormattedDictionary(snmpDevice, {'1': 'PoEGroup1'})                
        
        self.log.printInfo('Merge with previous data')
        snmpDevice.dictMerge(data, pethGrp)

        self.log.decreaseLevel()
        
        #== RETURNING RESULT ==========================

        sqlArray = {}
        sqlArray[self.deviceDescr] = {}                
        sqlArray[self.deviceDescr][self.devNumber] =  data
        sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
        sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
        sqlArray["ReadError"] = False   
        return sqlArray




        
        """
        test.filterBySnmpObject(    6,
                                    lib_SNMP.SNMPTable.FILTER_KEEP,
                                    lib_SNMP.SNMPTable.FILTER_BY_RAWVALUE,
                                    '.1.3.6.1.2.1.2.2.1.3',                                            
                                    )
        test.filterByTag('.1.3.6.1.2.1.2.2.1.3', lib_SNMP.SNMPTable.FILTER_REMOVE)
        #test.filterByTag([".1.3.6.1.2.1.2.2.1.2", ".1.3.6.1.2.1.2.2.1.8"], lib_SNMP.SNMPTable.FILTER_KEEP)
        pprint.pprint(test.getFormattedDictionary('.1.3.6.1.2.1.31.1.1.1.1'))
        """




        '''
        #loop over outlets
        if outletCount is not None:
                for x in range(1, int(outletCount) + 1):
                        self.getDataDict["outlet" + str(x)] = {}
                        self.getDataDict["outlet" + str(x)]['name']     = '1.3.6.1.4.1.13742.6.3.5.3.1.3.1.'  + str(x)
                        self.getDataDict["outlet" + str(x)]['status']   = '1.3.6.1.4.1.13742.6.4.1.2.1.2.1.'  + str(x)  #0 off, 1 on, 2 offWait, 3 onWait, 4 offError, 5 On Error, 6nocomm, 7 reading, 8 offFuse, 9 onFuse
                        self.getDataDict["outlet" + str(x)]['uptime']   = '1.3.6.1.4.1.13742.6.4.1.2.1.4.1.' + str(x)  #0 idleOff, 1 idleOn, 2 wakeOff, 3 wakeOn, 4 off, 5 on, 6 lockedOff, 7 lockedOn, 8 reboot, 9 shutdown, 10 pendOn, 11 pendOff, 12 minimumOff, 13 minimumOn, 14 eventOff, 15 eventOn, 16 eventReboot, 17 eventShutdown
        '''

'''
    def DoCmd(self, command = None, returnValue = None):
        if "Command" in command:                        
                if (command["Command"] == "rebootoutlet"):
                        returnValue = self.RebootOutlet(command)                        
        
        return super(self.__class__,self).DoCmd(command, returnValue)                
'''

'''
    def RebootOutlet(self, command):                            
        if "Option" in command:
                #isinstance(command["Option"],( int, long )):
                if command["Option"].isdigit(): 
                        id = int(command["Option"])                               

                        #get number of outputs
                        snmpDevice = lib_SNMP.SNMPv2(self.ipaddr)
                        outletCount = snmpDevice.readSNMP(self.getDataDict['OutletCount'])

                        if outletCount is not None:
                                outletCount = int(outletCount)

                        if id > 0 and id <= outletCount:  
                                self.log.printInfo("Rebooting outlet %s" % id)
                                #outletControlAction 1.3.6.1.4.1.1718.3.2.3.1.11.1.1.1-8
                                # readWrite ! - 0 none, 1 on, 2 off, 3 reboot
                                oid = netsnmp.Varbind('.1.3.6.1.4.1.13742.6.4.1.2.1.2.1.' + str(id),'','2','INTEGER')
                                res = netsnmp.snmpset(oid, version=2, hostname=self.ipaddr, community='RadioHolland')

                                return False
                else:
                        self.log.printWarning("Given outlet was not a number")
                        return True
        else:
                self.log.printWarning("No outlet-number was given")
                return True  

'''
