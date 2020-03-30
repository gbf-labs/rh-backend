import Class_GPS
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
import gps
import lib_Timeout


class GPSDeamon(Class_GPS.GPS):

        def __init__(self, INI, deviceDescr, devNumber):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                #for inhiretance from device class
                self.INI = INI
                self.deviceDescr = deviceDescr
                self.devNumber = devNumber       
                self.log.increaseLevel()                
        
        def Connect(self):
                """
                        Called from device-class
                        returns True if failed
                """
                
                #get vars out of INI
                ipaddr   = self.INI.getOption(self.deviceDescr, self.devNumber, "IP")   #localhost
                port     = self.INI.getOption(self.deviceDescr, self.devNumber, "PORT") #2947

                #check ini vars
                if None in (ipaddr, port):
                        self.Error = True
                        self.log.printError("Error: IP (= %s) and/or Port (= %s) is missing in INI-Files" % (ipaddr, port))
        
                try:
                        with lib_Timeout.Timeout(10):  # <<== Time given in seconds 
                                if self.Error == False:# default: Listen on port 2947 (gpsd) of localhost
                                        self.session = gps.gps(ipaddr, port)
                                        self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
                                        return self.Error
                except lib_Timeout.Timeout.Timeout:
                        self.log.printError("ERROR Timeout in GPSDeamon Data,%s Module Error" % sys._getframe().f_code.co_name)                                
                        self.Error = True
                        Error["ReadError"] = True
                        return Error
                except Exception as e:
                        self.log.printError("ERROR during connecting GPSDeamon on %s " % str(ipaddr) + str(port))
                        self.log.printError( str(e))
                        self.Error = True
                        Error["ReadError"] = True
                        return Error

        def GetData(self):
                gpsData = {}
                #see also http://www.catb.org/gpsd/gpsd_json.html
                gpsData["ReadError"] = False
                counter = 0
                Error = {}                
                while True:
                        try:
                                with lib_Timeout.Timeout(10):  # <<== Time given in seconds 
                                        report = self.session.next()                                
                                        if report['class'] == 'TPV':

                                                """
                                                class	Yes	string	Fixed: "TPV"
                                                device	No	string	Name of originating device.
                                                status	No	numeric	GPS status: %d, 2=DGPS fix, otherwise not present.
                                                mode	Yes	numeric	NMEA mode: %d, 0=no mode value yet seen, 1=no fix, 2=2D, 3=3D.
                                                time	No	string	Time/date stamp in ISO8601 format, UTC. May have a fractional part of up to .001sec precision. May be absent if mode is not 2 or 3.
                                                ept	No	numeric	Estimated timestamp error (%f, seconds, 95% confidence). Present if time is present.
                                                lat	No	numeric	Latitude in degrees: +/- signifies North/South. Present when mode is 2 or 3.
                                                lon	No	numeric	Longitude in degrees: +/- signifies East/West. Present when mode is 2 or 3.
                                                alt	No	numeric	Altitude in meters. Present if mode is 3.
                                                epx	No	numeric	Longitude error estimate in meters, 95% confidence. Present if mode is 2 or 3 and DOPs can be calculated from the satellite view.
                                                epy	No	numeric	Latitude error estimate in meters, 95% confidence. Present if mode is 2 or 3 and DOPs can be calculated from the satellite view.
                                                epv	No	numeric	Estimated vertical error in meters, 95% confidence. Present if mode is 3 and DOPs can be calculated from the satellite view.
                                                track	No	numeric	Course over ground, degrees from true north.
                                                speed	No	numeric	Speed over ground, meters per second.
                                                climb	No	numeric	Climb (positive) or sink (negative) rate, meters per second.
                                                epd	No	numeric	Direction error estimate in degrees, 95% confidence.
                                                eps	No	numeric	Speed error estinmate in meters/sec, 95% confidence.
                                                epc	No	numeric	Climb/sink error estimate in meters/sec, 95% confidence.
                                                """

                                                if hasattr(report, "time"):
                                                        #Time/date stamp in ISO8601 format, UTC. May have a fractional part of up to .001sec precision. May be absent if mode is not 2 or 3
                                                        self.log.printOK("Setting system time to GPS time. (" + report["time"] + ")")
                                                        if False:
                                                                os.system('sudo date --set="' + report["time"] + '" > /dev/null')


                                                #fields = ["device", "status", "mode", "time", "ept", "lat", "lon", "alt", "epx", "epy", "epv", "track", "speed", "climb", "epd", "eps", "epc"]
                                                fields = ["lon", "lat", "status",  "mode",  "time",  "speed","track"] #    "device",  "time", "ept", , , "alt", "epx", "epy", "epv", , , "climb", "epd", "eps", "epc"]
                                                for field in fields:
                                                        if hasattr(report, field):
                                                                gpsData[field] = report[field]
                                                                #self.log.printInfo(str(field) + ":\t\t" + str(report[field]));
                                                        else:
                                                                gpsData[field] = None
                                                                #self.log.printInfo(str(field) + ":\t\t" + "-");
                                                
                                                break
                        except lib_Timeout.Timeout.Timeout:
                                self.log.printError("ERROR Timeout in GPSDeamon Data,%s Module Error" % sys._getframe().f_code.co_name)                                
                                self.Error = True
                                Error["ReadError"] = True
                                break;
                        except Exception as e:
                                self.log.printError("ERROR in Retreiving GPSDeamon Data,%s Module Error" % sys._getframe().f_code.co_name)
                                self.log.printError( str(e))
                                self.Error = True
                                Error["ReadError"] = True
                                break;
                                
                if self.Error:                       
                        return Error
                else:  
                        sqlArray = {}
                        sqlArray[self.deviceDescr] = {}
                        sqlArray[self.deviceDescr][self.devNumber] = {}
                        sqlArray[self.deviceDescr][self.devNumber]["General"] = gpsData
                        sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"] = {}
                        sqlArray[self.deviceDescr][self.devNumber]["_ExtractInfo"]["ExtractTime"] = time.time()
                        sqlArray["ReadError"] = False    
                        return sqlArray

                       