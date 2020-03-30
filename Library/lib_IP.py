
import re


import pprint

#
# Input:  10.8.0.1:
# Output: 168296449
#
def ConvertLongToIP(longIn):
        returnValue = None
        try:
                temp = str((longIn & 0xff000000) >> 24 ) + "." +  str((longIn & 0x00ff0000) >> 16 ) + "." + str((longIn & 0x0000ff00) >> 8 ) + "." + str(longIn & 0x000000ff)
                returnValue = ValidIPv4Address(temp)       
                
        except:
                returnValue = None

        return returnValue

#
#expects number in (0-32)
#returns netmask in ip format (e.g. 255.255.254.0)
def BuildNetMaskIPv4(nmbrOfBits):        
        returnValue = None

        try:

                if nmbrOfBits in range(0,32+1):                
                        currentValue = 0b0                                              
                        for x in range(0, nmbrOfBits + 1):
                                currentValue = currentValue * 2 + 0b1                                                              
                        for x in range(nmbrOfBits + 1, 32 +1):
                                currentValue = currentValue * 2

                        #returnValue =  str((currentValue & 0xff000000) >> 24 ) + "." +  str((currentValue & 0x00ff0000) >> 16 ) + "." + str((currentValue & 0x0000ff00) >> 8 ) + "." + str(currentValue & 0x000000ff)
                        returnValue = ConvertLongToIP(currentValue)
                else:
                        return None
        except:
                return None

        return returnValue


#
# Input:  10.8.1.1:
# Output: 00001010000010000000000100000001
#
def ConvertIPToBinaryString(IPAddress):
        returnValue = None
        try:

                isIPv4 = ValidIPv4Address(IPAddress)       
                if isIPv4 is not None: #if IP e.g. 255.255.0.0
                        exploded = isIPv4.strip().split(".")

                        #convert to integers
                        exploded = map(int, exploded)    
                        #convert to long string with 0b11110000                         
                        converted = "";
                        for x in exploded:
                                converted += bin(x)[2:].zfill(8)        
                        returnValue = converted

        except:
                returnValue = None

        return returnValue

#
# Input:  10.8.0.1:
# Output: 168296449
#
def ConvertIPToLong(IPAddress):
        returnValue = None
        try:
                isIPv4 = ValidIPv4Address(IPAddress)       
                if isIPv4 is not None: #if IP e.g. 255.255.0.0                        
                        exploded = isIPv4.strip().split(".")

                        #convert to integers
                        exploded = map(int, exploded)    
                        #convert to long string with 0b11110000                         
                        converted = 0;
                        for x in exploded:                                
                                converted = converted * 256  + x
                        returnValue = converted
        except:
                returnValue = None

        return returnValue

def ValidIPv4Address(IPAddress):        
        try:
                #split in bytes
                regex = r"^(?P<byte1>[0-9]{1,3})\.(?P<byte2>[0-9]{1,3})\.(?P<byte3>[0-9]{1,3})\.(?P<byte4>[0-9]{1,3})$"
                regexGroups = re.search(regex, IPAddress)        
                octets = {1: None, 2: None, 3: None, 4: None}

                #try to find the 4 bytes
                try:
                        octets[1] = regexGroups.group("byte1")
                        octets[2] = regexGroups.group("byte2")
                        octets[3] = regexGroups.group("byte3")
                        octets[4] = regexGroups.group("byte4")                
                except:                
                        return None

                #if 1 or more bytes doesn't exists
                if None in octets:                
                        return None

                #check if bytes are 0-255
                for octetNmbr in octets:                
                        if int(octets[octetNmbr]) not in range(0,255 + 1):                        
                                return None
        except:
                return None

        #if all previous checks are passed, the ip is valid
        return IPAddress

def ValidIPv4NetMask(netMask): 

        isIPv4 = ValidIPv4Address(netMask)       
        if isIPv4 is not None: #if IP e.g. 255.255.0.0                
                netMaskIPv4 = isIPv4
                netMaskIPv4BinStr = ConvertIPToBinaryString(isIPv4)
                netMaskGeneratedBinStr = ConvertIPToBinaryString(BuildNetMaskIPv4(netMaskIPv4BinStr.count('1')))

                if netMaskIPv4BinStr != netMaskGeneratedBinStr:
                        return None

        else:
                nmbrOfBits = None
                if isinstance(netMask, ( int, long ) ): #if input is int: e.g. : 24                        
                        nmbrOfBits = netMask
                elif isinstance(netMask, (str)): #if input is string e.g. "24"
                        if netMask.isdigit():
                                nmbrOfBits = int(netMask)
                        else:
                                nmbrOfBits = None   
                                return None    
                else:
                        return None

                if nmbrOfBits in (None, None, "") or nmbrOfBits not in range(0,32+1):
                        return None

                netMaskIPv4 = BuildNetMaskIPv4(nmbrOfBits)

        #if all previous checks are passed, the ip is valid
        return netMaskIPv4


#Checks if IPAddress1 falls in the same network as IPAddress2 with NetMask NetMask
#returns networkAddress if they are on the same network
def CheckIfIPInNetwork(IPAddress1, IPAddress2, Netmask):
        returnValue = None

        if None in (ValidIPv4Address(IPAddress1), ValidIPv4Address(IPAddress2)):
                print("IP1, I2, NetMask not valid")
                return None

        Netmask = ValidIPv4NetMask(Netmask)

        if Netmask is None:
                print("Netmask not valid")
                return None



        networkAddress1 = ConvertIPToLong(IPAddress1) & ConvertIPToLong(Netmask)
        networkAddress2 = ConvertIPToLong(IPAddress2) & ConvertIPToLong(Netmask)

        if networkAddress1 != networkAddress2:
                return None
        else:
                returnValue =  ConvertLongToIP(networkAddress1)


        return returnValue


#Checks if multicast address
#IPv4 multicast addresses are defined by the leading address bits of 1110, originating from the classful network design of the early Internet when this group of addresses was designated as Class D. The Classless Inter-Domain Routing (CIDR) prefix of this group is 224.0.0.0/4. The group includes the addresses from 224.0.0.0 to 239.255.255.255. 
def CheckIfIPIsMulticastAddress(IPAddress1):        
        tempValue =  CheckIfIPInNetwork(IPAddress1, "224.0.0.0", 4)
        if tempValue == None:
                return False
        else:
                return True

