import sys
from parse import *
import ConfigParser
import re 
import cStringIO
import StringIO
import os
import lib_Log
import lib_Parsing

def Cut_Multiline_String(String,Begin = None, End = None):
    try:
        Part1String = ""
        Start = False
        
        if Begin != None:
            length = len(Begin)
            for line in cStringIO.StringIO(String):
                a = 0
                while ( (line[a:a+1] == " ") or (line[a:a+1] == "\t") or (line[a:a+1] ) == ":"):
                    a = a+1
                line = line [a:]
                if Start == True:
                    Part1String += line
                if line[0:length] == Begin:
                    Start = True
        else:

            Part1String = String

        result = ""
        Stop = True
        if End != None:
            length = len(End)
            for line in cStringIO.StringIO(Part1String):
                if line[0:length] == End:
                    Stop = False
                if Stop == True:
                    result += line
                    
            return result   
        else:
            return Part1String
    except:
        return None

def String_Parse(String = "",OriginalKeys = "",ReplaceKeys = "",Section = "TEMP"):

    try:
        log = lib_Log.Log(PrintToConsole=True)
        log.increaseLevel()
        Value = {}
        temp = ""
        for line in cStringIO.StringIO(String):
            a = 0
            while ( (line[a:a+1] == " ") or (line[a:a+1] == "\t") or (line[a:a+1] ) == ":" or (line[a:a+1] ) == ">"):
                a = a+1
            line = line [a:]
            
            
            if (line [0:1] == "="):
                line = lib_Parsing.Get_Var_String(line)
            #ignore if modem session (iDirect)
            if (line [0:5] != "[RMT:") :
                temp = temp + line

        String = temp
        String = "[TEMP]" + "\n" + String
        buf = StringIO.StringIO(String)
        config = ConfigParser.ConfigParser()
        config.readfp(buf)
        
        for a in OriginalKeys :
            try:
                Value[a] = (config.get(Section, a)) 
            except:
                Value[a] = None
        
        i = 0
        end = len (OriginalKeys)
        Result = {}
        for keys in Value:
            Result[(ReplaceKeys[i])] = Value[OriginalKeys[i]]
            if Result[(ReplaceKeys[i])] is None:
                Result.pop (ReplaceKeys[i],None)
                log.printWarning("%s Value was not found and have been removed" % ReplaceKeys[i])
            i = i +1
            if i >= end:
                break
        
        return Result

    except Exception as e: 

        #log.printError( str(e))
        log.printWarning("Can not parse string : %s" % String)
        return None

    
def Get_Var_String(String = ""):  
    log = lib_Log.Log(PrintToConsole=True)
    String = re.sub('[=]', '', String) 
    #Remove space in beginning and ending, and the \n
    #String = String[1:-2]
    String = String.strip()
    String = "[" + String + "]\n"
    return String
    
    
            
    
def String_WithSection_Parse(String,device, parameters):
    log = lib_Log.Log(PrintToConsole=True)
    buf = StringIO.StringIO(String)
    Config = ConfigParser.ConfigParser()
    Config.readfp(buf)
    try:
        returnValue = {}
        #if Info# 
        unqiueSection = False
        if "#" in device:
            device = device.replace("#","")
            regex = "^" + device + '$'
            unqiueSection = True                                                                                                
        else:
            regex = "^" + device + '[0-9]+$'
        #loop over ini files
        for confFile in Config:
            #loop over sections
            for section in Config[confFile].sections():
                #filter out non-valid sections
                #str matches - e.g. Switch1

                if re.match(regex.lower(), section.lower()):
                    #get number of device
                    #section = Switch1, Switch2, ...
                    if unqiueSection:
                        number = -1
                    else:
                        number = int(section.replace(device, ""))
                        
                    returnValue[number]={}
                    #loop over parameters
                    for var in parameters:
                        subParameters = parameters[var]
                        key = subParameters['key'].lower()
                        type = subParameters['type'].lower()
                        
                        if Config[confFile].has_option(section, key):
                            if (type == "str") :
                                returnValue[number][var] =  Config[confFile].get(section, key)
                            elif (type == "int") :
                                returnValue[number][var] =  Config[confFile].getint(section, key)
                            elif (type == "float") :
                                returnValue[number][var] =  Config[confFile].getfloot(section, key)                                                                
                            elif (type == "bool") :
                                returnValue[number][var] =  Config[confFile].getboolean(section, key)                                                                
                            else:
                                returnValue[number][var] =  Config[confFile].get(section, key)
        
        #check if all parameters are defined for each device
        for deviceNumber in returnValue:
            returnValue[deviceNumber]["Error"] = False
            for var in parameters:
                if var in returnValue[deviceNumber]:
                    pass
                else:
                    msg = "Warning: " + var + " not defined for " + device
                    if (deviceNumber == -1):
                        msg += str(deviceNumber)                                                
                    
                    self.log.printError(msg)
                    returnValue[deviceNumber]["Error"] = True
            
            if (deviceNumber == -1):
                returnValue = returnValue[-1]
                break;
                    
    except:
        self.log.printError("%s Module Error" % sys._getframe().f_code.co_name) 
        returnValue = False
            
    return returnValue

def TimeSting_To_Sec(String,CleanUp = True):
    try:
        log = lib_Log.Log(PrintToConsole=True)
        if CleanUp:
            b = parse("{days} days {hours} hrs {minutes} mins {seconds} secs", String)
            if b == None:
                b = parse("{hours} hrs {minutes} mins {seconds} secs", String)
                if b == None:
                    b = parse("{minutes} mins {seconds} secs", String)
                    if b == None:
                        time = 0
                    else:
                        result = "0D 0H " + b["minutes"] + "M " + b["seconds"] + "S"

                else :
                        result = "0D " + b["hours"] + "H " + b["minutes"] + "M " + b["seconds"] + "S"
                    
            else:
                result = b["days"] + "D " + b["hours"] + "H " + b["minutes"] + "M " + b["seconds"] + "S"
                
        b = parse("{days}D {hours}H {minutes}M {seconds}S", result)
        if b == None:
            time = 0
        else:
            Time = (float(b["days"]) * 86400) + (float(b["hours"]) * 3600 ) + (float(b["minutes"]) * 60) + float(b["seconds"])
        return Time
    except Exception as e: 
        log.printError("%s Module Error" % sys._getframe().f_code.co_name) 
        log.printError( str(e))

