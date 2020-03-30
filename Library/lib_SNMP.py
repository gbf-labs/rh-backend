
import netsnmp
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
class SNMPv2 (object):
        def __init__(self, DestHost):
            self.log = lib_Log.Log(PrintToConsole=True)
            self.Error = False                
            self.log.increaseLevel()                
            self.destHost = DestHost

            #new from here
            self.community = 'public'
            self.remotePort = 161
            self.snmpVersion = 2 #2 => 2c

            self.tables = {}
            
            self.snmpSession = netsnmp.Session(Version=self.snmpVersion,
                                                DestHost=self.destHost, 
                                                Community=self.community,
                                                RemotePort = self.remotePort,
                                                Timeout = 500000, #micro-sec
                                                Retries = 2,
                                                UseNumeric = 1,  #using OIDs                                                                                          
                                                )

            
            self.oidConversion = {}
                                     

            self.textualConversion = {}
            self.textualConversion['ifMib_ifAdminStatus']                           = {1 : 'up',    2: 'down',  3: 'testing'    }
            self.textualConversion['ifMib_ifOperStatus']                            = {1 : 'up',    2: 'down',  3: 'testing',   4: 'unknown',   5: 'dormant',   6: 'notPresent',    7: 'lowerLayerDown' }
            self.textualConversion['ifMib_IANAifType']                              = {1 : 'other', 6: 'ethernetCsmacd',        33: 'rs232',    53: 'propVirtual'     }
            self.textualConversion['PowerEthernetMib_pethPsePortAdminEnable']       = {1 : 'true',  2: 'false'    }
            self.textualConversion['PowerEthernetMib_pethPsePortDetectionStatus']   = {1 : 'disabled',          2: 'searching', 3: 'deliveringPower', 4: 'fault', 5: 'test', 6: 'otherFault'}
            self.textualConversion['PowerEthernetMib_pethMainPseOperStatus']        = {1 : 'on',    2: 'off',  3: 'faulty'    }
            self.textualConversion['EntityMib_entPhysicalClass']                    = {1: 'other', 2: 'unkown', 3: 'chassis', 4: 'backplane', 5: 'container', 6: 'powerSupply', 7: 'fan', 8: 'sensor', 9: 'module', 10: 'port', 11: 'stack', 12: 'cpu'}
            self.textualConversion['QBridgeMib_dot1qVlanStatus']                    = {1: 'other', 2: 'permanent', 3: 'dynamicGvrp'}

            #general SNMPv2MIB definition
            self.oidConversion.update({
                                '.1.3.6.1.2.1.1.1' : {'name': 'sysDescr'},
                                '.1.3.6.1.2.1.1.2' : {'name': 'sysObjectID'},
                                '.1.3.6.1.2.1.1.3' : {'name': 'sysUptime'},
                                '.1.3.6.1.2.1.1.4' : {'name': 'sysContact'},
                                '.1.3.6.1.2.1.1.5' : {'name': 'sysName'},
                                '.1.3.6.1.2.1.1.6' : {'name': 'sysLocation'},
                                '.1.3.6.1.2.1.1.7' : {'name': 'sysServices'},
                            })
                             
            self.SNMPv2MIB_varList = netsnmp.VarList(
                                                        netsnmp.Varbind('.1.3.6.1.2.1.1.1'),
                                                        #netsnmp.Varbind('.1.3.6.1.2.1.1.2'),
                                                        netsnmp.Varbind('.1.3.6.1.2.1.1.3'),
                                                        netsnmp.Varbind('.1.3.6.1.2.1.1.4'),
                                                        netsnmp.Varbind('.1.3.6.1.2.1.1.5'),
                                                        netsnmp.Varbind('.1.3.6.1.2.1.1.6'),
                                                        #netsnmp.Varbind('.1.3.6.1.2.1.1.7'),                                                        
                                                        )


        def readSNMP(self, oid, community='public'):              					
            oid = '.' + oid
            oidList = netsnmp.Varbind(oid)
            res = netsnmp.snmpget(oidList, Version=2, DestHost=self.destHost , Community=community)

            #debug command
            #snmpwalk -v2c -c public 192.168.0.100 1.3.6.1.4.1.1718.3.2.3.1

            if res == ():
            	res = None
            else:
            	res = res[0]

            return res

        '''
        def convertOidArrayToVarList(self, oidArray):
            oidTuple = ( )
            for oid, parameters in oidArray.iteritems():                
                newOidTuple = tuple([netsnmp.Varbind(oid)])                
                oidTuple = oidTuple + newOidTuple                

            
            #varList = netsnmp.VarList(oidTuple) <-- crashes
            return varList;
        '''

        def getWalk_SNMPv2MIB(self):
            return self.getWalkMultiple(self.SNMPv2MIB_varList)      

        def getWalkSingle(self, oid ):            
            varList = netsnmp.VarList(netsnmp.Varbind(oid))            
            self.snmpSession.walk(varList)
            return self.formatVarListResult(varList)

        def getWalkMultipleRaw(self, varList ):
            self.snmpSession.walk(varList)
            return varList

        def getWalkMultiple(self, varList):            
            return self.formatVarListResult(self.getWalkMultipleRaw(varList))

        def initTable(self, tableName):
            self.tables[tableName] = SnmpTable()
            return self.tables[tableName]

        def initQBridgeTable(self, tableName):
            import lib_SNMP_QBridgeMib
            self.tables[tableName] = lib_SNMP_QBridgeMib.QBridgeMibTable()
            return self.tables[tableName]

        def fillTable(self, tableName):
            varList = self.getWalkMultipleRaw(self.tables[tableName].getVarList())                  
            return self.tables[tableName].sortByRow(varList)

        def getTable(self,tableName):
            return self.tables[tableName]


        """
        def getTable(self, snmpTable):            
            varList = self.getWalkMultipleRaw(snmpTable.getVarList())
            #pprint.pprint(varList)
            return snmpTable.sortByRow(varList)
            #return "" #self.formatVarListResult(varList)
        """
        def getOidConversion(self, oidIn):
            returnValue = oidIn                    
            strippedOidIn = oidIn.rstrip('.0')
            for tag, params in self.oidConversion.iteritems():                
                if tag == strippedOidIn:                    
                    returnValue = params.get('name', oidIn)
                    break
            return returnValue


        def updateOidConversion(self, newValues):
            dictMerge(self.oidConversion, newValues)

        def dictMerge(self, dct, merge_dct):
            """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
            updating only top-level keys, dict_merge recurses down into dicts nested
            to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
            ``dct``.
            :param dct: dict onto which the merge is executed
            :param merge_dct: dct merged into dct
            :return: None
            """
            for k, v in merge_dct.iteritems():
                if (k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], collections.Mapping)):
                    self.dictMerge(dct[k], merge_dct[k])
                else:
                    dct[k] = merge_dct[k]


        def textualConversionToValue(self, textualConversionTableName, text):            
            temp = self.textualConversion.get(textualConversionTableName, {})            
            result = temp.keys()[temp.values().index(text)]            
            return result

        """
            Formats varList for netSnmpfunction

            Returns dictionary with following format:
                {
                    '.1.3.6.1.2.1.1.1.0': { 'iid': '0',
                                            'oid': '.1.3.6.1.2.1.1.1.0',
                                            'rawvalue': 'SG300-52P 52-Port Gigabit PoE Managed Switch',
                                            'tag': '.1.3.6.1.2.1.1.1',
                                            'type': 'OCTETSTR'},
                    '.1.3.6.1.2.1.1.3.0': { 'iid': '0',
                                            'oid': '.1.3.6.1.2.1.1.3.0',
                                            'rawvalue': '43528600',
                                            'tag': '.1.3.6.1.2.1.1.3',
                                            'type': 'TICKS'},
                    ...
                }
        """
        def formatVarListResult(self, varList):            
            result = {}
            for var in varList:
                #fullOid = var.tag + '.' + var.iid
                #result.update({fullOid: {'oid' : fullOid, 'tag': var.tag, 'iid' : var.iid, 'rawvalue' :var.val, 'type': var.type}})
                snmpObject = SNMPObject()
                snmpObject.setFromVarBind(var)

                result.update({snmpObject.oid: snmpObject})
                del snmpObject
                

            return result            

        def getFormattedDictionary(self, dictIn):
            returnValue = {}
            for key, value in dictIn.iteritems():                
                returnValue[self.getOidConversion(key)] = value.convertedValue()


                #returnValue[self.getoidConversion(key)] = value

            return returnValue


        '''
            Get Bulk function
            The GETBULK operation is normally used for retrieving large amount of data, particularly from large tables. A GETBULK request is made by giving an OID list along with a Max-Repetitions value and a Nonrepeaters value.

            Arguments:
                varList
                            varList of varBindings (see netsnmp)
                            or a dictionary in following format:
                                {
                                    'varList'= ...VARLIST...,
                                    'nonrepeater' = <integer>,
                                    'maxrepetitions' = <integer>
                                } 
                nonrepeaters
                            optional (used as default value) when varlist is dictionary
                            The Nonrepeaters value determines the number of variables in the variable list for which a simple GETNEXT operation has to be done
                maxrepetitions
                            optional (used as default value) when varlist is dictionary
                            For the remaining variables, the continuous GETNEXT operation is done based on the Max-Repetitions value

        '''
        def getBulk(self, varList, nonrepeaters = 1, maxrepetitions = 0):

            #check if varList is dictionary
            if isinstance(varList,dict):
                nonrepeaters = varList.get('nonrepeaters', nonrepeaters)
                maxrepetitions = varList.get('maxrepetitions', maxrepetitions)
                varList = varList.get('varList', None)

            self.snmpSession.getbulk(nonrepeaters,maxrepetitions, varList)
            return self.formatVarListResult(varList)            


        '''
        def getBulk2(self):
            vars = netsnmp.VarList(netsnmp.Varbind('sysUpTime'),
                                    netsnmp.Varbind('sysORLastChange'),
                                    netsnmp.Varbind('sysORID'),
                                    netsnmp.Varbind('sysORDescr'),
                                    netsnmp.Varbind('sysORUpTime'))
            vals = self.snmpSession.getbulk(2, 8, vars)
            print "v2 sess.getbulk result: ", vals, "\n"
            return
        '''


class SnmpTable (object):
    FILTER_KEEP = False  #for a filter, keep the found results
    FILTER_REMOVE = True #for a filter, remove the found results    
    FILTER_BY_TAG = 'tag'
    FILTER_BY_IID = 'iid'
    FILTER_BY_OID = 'oid'
    FILTER_BY_RAWVALUE = 'rawValue'
    FILTER_BY_RAWTYPE = 'rawType'
    FILTER_WHERE_ALL = None
    FILTER_WHERE_INVERTED = True
    FILTER_WHERE_NOTINVERTED = False
    FILTER_REMOVE_IID = 'IID'
    FILTER_REMOVE_TAG = 'TAG'


    def __init__(self):
        self.mainOID = ''
        self.subOIDs = {}
        self.table = {}
            

    """
        PRESETS
    """
    """
    def presetIfMib(self):
        self.mainOID = '.1.3.6.1.2.1.2.2.1'
        self.subOIDs = {'1':  {},   #ifIndex
                        '2':  {},   #ifDescr
                        '3':  {},   #ifType
                        '4':  {},   #ifMTU
                        '5':  {},   #ifSpeed
                        '6':  {},   #ifPhysAddress
                        '7':  {},   #ifAdminStatus
                        '8':  {},   #ifOperStatus
                        '9':  {},   #ifLastChange
                        }
        self.table = {}       
    """ 

    def presetIfMib(self):
        self.mainOID = '.1.3.6.1.2.1'
        self.subOIDs = {'2.2.1.1':  {'name' : 'ifIndex'         },   #ifIndex
                        '2.2.1.2':  {'name' : 'ifDescr'         },   #ifDescr
                        '2.2.1.3':  {'name' : 'ifType',         'textualConversion' : 'ifMib_IANAifType'    },   #ifType
                        '2.2.1.4':  {'name' : 'ifMTU'           },   #ifMTU
                        '2.2.1.5':  {'name' : 'ifSpeed'         },   #ifSpeed
                        '2.2.1.6':  {'name' : 'ifPhysAddress'   },   #ifPhysAddress
                        '2.2.1.7':  {'name' : 'ifAdminStatus',  'textualConversion' : 'ifMib_ifAdminStatus'       },   #ifAdminStatus
                        '2.2.1.8':  {'name' : 'ifOperStatus',   'textualConversion' : 'ifMib_ifOperStatus'  },   #ifOperStatus
                        '2.2.1.9':  {'name' : 'ifLastChange'    },   #ifLastChange
                        '31.1.1.1.1' : {'name' : 'ifName'       },   #ifName
                        '31.1.1.1.15' : {'name' : 'ifHighSpeed' },
                        }        

    def presetEntityMib(self):
        self.mainOID = '.1.3.6.1.2.1.47.1.1.1.1'
        self.subOIDs = {
                        '2':  {'name' : 'entPhysicalDescr'},
                        '6':  {'name' : 'entPhysicalParentRelPos'},
                        '5':  {'name' : 'entPhysicalClass',         'textualConversion' : 'EntityMib_entPhysicalClass'},
                        '7':  {'name' : 'entPhysicalName'},
                        '8':  {'name' : 'entPhysicalHardwareRev'},
                        '9':  {'name' : 'entPhysicalFirmwareRev'},
                        '10':  {'name' : 'entPhysicalSoftwareRev'},
                        '11':  {'name' : 'entPhysicalSerialNum'},
                        '12':  {'name' : 'entPhysicalMfgName'},
                        '13':  {'name' : 'entPhysicalModelName'},
                        '14':  {'name' : 'entPhysicalAlias'},
                        }                        

    def presetPowerEthernetMib(self):
        self.mainOID = '.1.3.6.1.2.1.105'
        self.subOIDs = {'1.1.1.3.1':  {'name' : 'pethPsePortAdminEnable',         'textualConversion' : 'PowerEthernetMib_pethPsePortAdminEnable'},
                        '1.1.1.6.1':  {'name' : 'pethPsePortDetectionStatus' ,    'textualConversion' : 'PowerEthernetMib_pethPsePortDetectionStatus'},                        
                        }

    def presetPowerEthernetGroupMib(self):
        self.mainOID = '.1.3.6.1.2.1.105.1.3.1.1'
        self.subOIDs = {
                        '2':  {'name' : 'pethMainPsePower'},
                        '3':  {'name' : 'pethMainPseOperStatus',                  'textualConversion' : 'PowerEthernetMib_pethMainPseOperStatus'},
                        '4':  {'name' : 'pethMainPseConsumptionPower'},
                        }

    
    def printTable(self):
        pprint.pprint(self.table)

    """
        getVarList
    """
    def getVarList(self):
        # https://github.com/haad/net-snmp/blob/master/python/netsnmp/client.py#L107 - search for append
        varList = netsnmp.VarList()
        for key in self.subOIDs:
            appendOid = self.mainOID + '.' + key                       
            varList.append(netsnmp.Varbind(appendOid))            

        return varList
    
    """
        Sort By Row
            For example: set everything from one RJ45-port in the same dictionary
    """                                                 
    def sortByRow(self, varList):
        #self.table = {}        
        for var in varList:                
                snmpObject = SNMPObject()                
                snmpObject.setFromVarBind(var)                                
                if var.iid not in self.table:
                    self.table.update({var.iid : {}})                    
                            
                self.table[var.iid].update({snmpObject.tag: snmpObject})                
                del snmpObject
        
        return self.table

    """
        filters table by filtering on tags.

        tags
            can be a list [] or string
        remove
            default true
            if true, remove all tags that are equal
            if false, keep all tags that are equal and remove the rest
    """    
    def filterByTag(self, tags, removeOrKeep = FILTER_REMOVE):
        if isinstance(tags, dict):
            tags = tags.values()
        if not isinstance(tags, list):
            tags = [tags]

        
        #convert tags from textual representation to Oid if needed
        self.convertTextualRepresentationListToOid(tags)
        
        #loop over table rows
        for iid in self.table.keys():
            colomnTags = self.table[iid].keys()
            tagsToRemove = []
            #loop over all columns and get tags
            for columnTag in colomnTags:
                tagFound = True if columnTag in tags else False
                #Check if should removed
                if ((tagFound and removeOrKeep) or (not tagFound and not removeOrKeep)):                    
                    tagsToRemove.append(columnTag)
                #Check if should keep
                if ((not tagFound and removeOrKeep) or (tagFound and not removeOrKeep)):
                    pass
                    
            #remove the needed tags
            for k in tagsToRemove:
                self.table[iid].pop(k, None)        
        return self.table


    """
        get's a formated dictionary
        snmpDevice
                a SNMPv2 instance
        moduleNameOid
                if None: use iid as module Name
                if string: can be name (e.g. 'ifName' of oid '.1.2.3.4')
                if dictionary: should be in following format:
                                {index : 'name'}
                                e.g.
                                {'1' : 'gi1', '2', 'gi2'}
                returns tuple
                    1st item: the result dictionary
                    2nd item: index mapping dictionary (can be used as moduleNameOid for a following getFormattedDictionary)
                        e.g. {'1' : 'gi1', '2', 'gi2'}

    """
    #def getFormattedDictionary(self, snmpDevice, moduleNameOid = None, filterOutModuleName = FILTER_REMOVE):        
    def getFormattedDictionary(self, snmpDevice, moduleNameOid = None, **kwargs):
        filterOutModuleName     = kwargs.get('filterOutModuleName', self.FILTER_REMOVE) #keep or remove the used moduleName out of the result values
        modulePrefix            = kwargs.get('modulePrefix', '')  #if moduleName is not a dictionary (or is a dictionary and nothing can be found), use this prefix if a value is found

        returnValue = {}
        indexMapping = {}
        moduleOid = None
        for iid, column in self.table.iteritems():                        
            for tag, snmpObject in self.table[iid].iteritems():  
                modulePrefix = modulePrefix if isinstance(modulePrefix, str) else ''              
                module = modulePrefix + iid                   
                if moduleNameOid is not None:                                        
                    if isinstance(moduleNameOid, dict):
                        module = moduleNameOid.get(iid, modulePrefix + iid)
                    else:
                        try:
                            moduleOid = self.convertTextualRepresentationListToOid([moduleNameOid])[0]
                            module = self.table[iid][moduleOid].convertedValue()                                        
                        except:
                            pass

                if module not in returnValue:
                    returnValue.update({module : {}})
                    indexMapping.update({iid : module})

                #option                                
                index = tag.replace(self.mainOID + '.', '')
                subOidDict = self.subOIDs.get(index, {})
                optionName = subOidDict.get('name', snmpObject.optionName)


                if not ((tag == moduleOid) and (filterOutModuleName is self.FILTER_REMOVE)):                                                    
                    #value                
                    textualConversionTableName = subOidDict.get('textualConversion', None)                
                    convertValueMethod = subOidDict.get('convertValueMethod', None)

                    convertedValue = snmpObject.convertedValue(snmpDevice, textualConversionTableName = textualConversionTableName, convertValueMethod = convertValueMethod)                
                    returnValue[module].update({optionName : convertedValue})
                    

        return returnValue, indexMapping

    def convertTextualRepresentationListToOid(self, listInput):        
        #convert tags from textual representation to Oid if needed
        i = 0
        while i < len(listInput):            
            tag = listInput[i]            
            for subOid in self.subOIDs:                                
                if ((tag is not None) and (self.subOIDs[subOid].get('name', None) is tag)): #see if can be replaced by oid
                    listInput[i] = self.mainOID + '.' + subOid
                    break
            i+=1
        return listInput 



    """
        filters table by filtering on raw.

        vals
            can be a list [] or string
        remove
            default true
            if true, remove all tags that are equal
            if false, keep all tags that are equal and remove the rest
    """    
    def filterBySnmpObject(self, searchValues, removeOrKeep = FILTER_REMOVE, filterBy = FILTER_BY_RAWVALUE, tagsWhere = FILTER_WHERE_ALL, whereInverted = FILTER_WHERE_NOTINVERTED, removeMethod = FILTER_REMOVE_IID):
        #cleanup searchValues (make list if dict or not list)
        if isinstance(searchValues, dict):
            searchValues = searchValues.values()
        if not isinstance(searchValues, list):
            searchValues = [searchValues]

        #convert everything to string in list
        searchValues = [str(i) for i in searchValues]

        #cleanup tagsWhere (make list if dict or not list)
        if tagsWhere is self.FILTER_WHERE_ALL:
            pass
        else:
            if isinstance(tagsWhere, dict):                
                tagsWhere = tagsWhere.values()
            if not isinstance(tagsWhere, list):
                tagsWhere = [tagsWhere]
        
        #convert tagsWhere from textual representation to Oid if needed
        self.convertTextualRepresentationListToOid(tagsWhere)
        
        #initiate
        iidsToRemove = []
        #loop over table rows
        for iid in self.table.keys():
            #get all tags (like column-ids)
            colomnTags = self.table[iid].keys()
            tagsToRemove = []
            #loop over all columns and get tags
            for columnTag in colomnTags:
                #where tag is....                
                if ((tagsWhere is self.FILTER_WHERE_ALL) or (columnTag in tagsWhere and not whereInverted) or (columnTag not in tagsWhere and whereInverted)):
                    #get snmpobject
                    snmpObject = self.table[iid][columnTag]

                    #get specific item of snmpObject to search for
                    searchObject = None
                    searchObject = snmpObject.tag       if filterBy is self.FILTER_BY_TAG       else searchObject
                    searchObject = snmpObject.iid       if filterBy is self.FILTER_BY_IID       else searchObject
                    searchObject = snmpObject.oid       if filterBy is self.FILTER_BY_OID       else searchObject
                    searchObject = snmpObject.rawValue  if filterBy is self.FILTER_BY_RAWVALUE  else searchObject
                    searchObject = snmpObject.rawType   if filterBy is self.FILTER_BY_RAWTYPE   else searchObject

                    #check if searchObject can be found
                    found = True if searchObject in searchValues else False

                    #Check if should removed
                    if ((found and removeOrKeep) or (not found and not removeOrKeep)):                                            
                        tagsToRemove.append(columnTag)
                        if(iid not in iidsToRemove):
                            iidsToRemove.append(iid)
                    #Check if should keep
                    if ((not found and removeOrKeep) or (found and not removeOrKeep)):
                        pass
            
            #remove tags if needed
            if removeMethod is self.FILTER_REMOVE_TAG:
                #remove the needed tags
                for k in tagsToRemove:
                    self.table[iid].pop(k, None)
        
        #remove iids if needed
        if removeMethod is self.FILTER_REMOVE_IID:
            #remove the needed iids        
            for k in iidsToRemove:
                self.table.pop(k, None)

        return self.table



class SNMPObject (object):
    def __init__(self):
        #self.__oid = None #private -> oid is function of tag and iid
        self.__tag = None #private
        self.__iid = None # private
        self.__rawValue = None #private
        self.__rawType = None #private        
        self.__forcedOptionName = None #private

    """
        GETTER's
    """
    @property
    def tag(self):  #getter
        return self.__tag
    
    @property 
    def iid(self): #getter
        return self.__iid

    @property 
    def rawValue(self): #getter        
        return self.__rawValue

    @property 
    def rawType(self): #getter        
        return self.__rawType  

    @property 
    def forcedOptionName(self): #getter        
        return self.__forcedOptionName


    """
        SETTER's
    """
    @tag.setter
    def tag(self, value):        
        self.__tag = value

    @iid.setter
    def iid(self, value):        
        self.__iid = value        

    @rawValue.setter
    def rawValue(self, value):                
        self.__rawValue = value

    @rawType.setter
    def rawType(self, value):        
        self.__rawType = value
    
    @forcedOptionName.setter
    def forcedOptionName(self, value):        
        self.__forcedOptionName = value        

    """
        Get OID
    """
    @property
    def oid(self): #getter - combination of tag and iid
        returnValue = ''
        returnValue += '' if self.tag is None else self.tag
        returnValue += '' if self.iid is None else '.'  + self.iid

        #set to None if nothing inside
        returnValue = None if returnValue is '' else returnValue        
        return returnValue        

    """
        Get converted value
    """
    
    def convertedValue(self, snmpDevice = None, **kwargs):
        textualConversionTableName      = kwargs.get('textualConversionTableName', None)
        convertValueMethod              = kwargs.get('convertValueMethod', None)

        returnValue = self.__rawValue    
        
        #RAW
        if (convertValueMethod == 'raw'):            
            return self.__rawValue

        #check if textuelConversionTableName is valid
        textualConversion = None

        if (    isinstance(snmpDevice, SNMPv2)
                and isinstance(textualConversionTableName, str)
                and snmpDevice.textualConversion.get(textualConversionTableName, None) is not None
            ):
            textualConversion = textualConversionTableName
        
        #INTEGER
        if self.__rawType == 'INTEGER':
            if textualConversion is not None:
                returnValue = snmpDevice.textualConversion.get(textualConversionTableName, {}).get(int(self.__rawValue), None)
                if returnValue is None:
                    returnValue = self.__rawValue
            return returnValue        

        #INTEGER32
        if self.__rawType == 'INTEGER32':
            pass            
            return returnValue

        #TICKS
        if self.__rawType == 'TICKS':
            try:                   
                #returnValue = float(self.__rawValue) * 0.01                
                x = float(self.__rawValue) * 0.01                
                returnValue = float("{0:.2f}".format(x))                
            except:
                returnValue = None
            return returnValue

        #OCTETSTR
        if self.__rawType == 'OCTETSTR':            
            onlyAscii = all(ord(char) < 128 for char in self.__rawValue) #check for non-asci chars (e.g. not the case with MAC-adresses)
            if not onlyAscii:
                convertedOctetString = repr(self.__rawValue).strip('\'')
                convertedOctetString = convertedOctetString.replace('\\\\', '\\x5c')  #fix when ascii-value = \

                #check if MAC address                        
                #regex = r"\A(((\\x[a-fA-F0-9]{2})|([a-zA-Z0-9]|\s)){6})\Z"  #search for 6 groups of hexadecimal chars or single ascii-char
                #regex = r"\A(((\\x[a-fA-F0-9]{2})|(.|\s)){6})\Z"  #search for 6 groups of hexadecimal chars or single ascii-char
                regex = r"\A(((\\x[a-fA-F0-9]{2})|(.|(\\[a-z^x]))){6})\Z"  #search for 6 groups of hexadecimal chars or single ascii-char
                matchMAC = re.search(regex, convertedOctetString)
                
                if matchMAC:
                    returnValue = self.convertOctetStrToMac(self.__rawValue)            
                
                return returnValue
                
         
        return returnValue

    """
        Get optionName
    """
    @property 
    def optionName(self): #getter
        #returnValue = self.oid
        returnValue = self.__forcedOptionName if self.__forcedOptionName is not None else self.oid                 
        return returnValue


    """
        fil this object using a varbind object
    """
    def setFromVarBind(self, varBindObject):
        if isinstance(varBindObject, netsnmp.client.Varbind):        
            self.iid = varBindObject.iid
            self.tag = varBindObject.tag
            self.rawValue = varBindObject.val
            self.rawType = varBindObject.type 
        else:
            print("Non valid varbind")
            return None
        return True

    def convertOctetStrToMac(self,inputStr):
            if inputStr == None:
                    return None
            try:
                    result = binascii.hexlify(inputStr)
                    s = ""
                    for i in range(0,12,2):
                        s += result[i:i+2] + ":"
                    result=s[:-1]
                    return result
                    
            except:
                    return None        

    """
        Conversion to string - mostly used for debugging
    """
    def __str__(self):
        returnValue = '('
        returnValue += '' if self.tag is None else self.tag
        returnValue += ')'
        returnValue += '' if self.iid is None else ( '.(' + self.iid + ')')
        returnValue += ' '
        returnValue += '' if self.oid is None else self.oid + ' '
        returnValue += '= '
        returnValue += '' if self.rawValue is None else self.rawValue
        returnValue += '' if self.rawType is None else ( ' [' + self.rawType + ']')

        return returnValue 
