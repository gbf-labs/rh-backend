import re

class Nmea(object):
	def __init__ (self,nmeaString,talkerID = None, identifier = None, protocol = "UDP"):
		#protocol can be NMEA-0183
		self.nmeaString = nmeaString
		self.talkerID = talkerID
		self.identifier = identifier
		self.protocol = protocol

		self.NMEASyntax = {}
		#Course over ground and ground speed
		self.NMEASyntax["VTG"] = ("courseOverGroundTrueDegrees", "true", "courseOverGroundMagneticDegrees", "magnetic", "speedOverGroundKnots", "knots", "speedOverGroundKph", "kph", "faaModeIndicator")
		#Course over ground and ground speed
		self.NMEASyntax["VTG_OLD"] = ("courseOverGroundTrueDegrees", "courseOverGroundMagneticDegrees", "speedOverGroundKnots", "speedOverGroundKph")
		#Depth below surface
		self.NMEASyntax["DBS"] = ("depthBelowSurfaceFeet", "feets", "depthBelowSurfaceMeter", "meter", "depthBelowSurfaceFathom", "fathoms")
		#Depth below transducer
		self.NMEASyntax["DBT"] = ("depthBelowTransducerFeet", "feets", "depthBelowTransducerMeter", "meter", "depthBelowTransducerFathoms", "fathoms")
		#Depth of water
		self.NMEASyntax["DPT"] = ("depthOfWaterRelativeToTransducerMeter", "depthOfWaterOffsetFromTransducerMeter", "maximumRangeScaleInUse")
		#GNSS DOP and active sattelilites
		#self.NMEASyntax["GSA"] = ("gpsSelectionMode", "gpsMode", "satID1", "satID2", "satID3", "satID4", "satID5", "satID6", "satID7", "satID8", "satID9", "satID10", "satID11", "satID12", "PDOPMeter", "HDOPMeter", "VDOPMeter")
		#Heading deviation and variation
		self.NMEASyntax["HDG"] = ("headingMagneticTrueDegrees", "magneticDeviationDegrees", "magneticDeviationDirection", "magneticVariationDegrees", "magneticVariationDirection")
		#Heading - Magnetic
		self.NMEASyntax["HDM"] = ("headingMagneticTrueDegrees", "magnetic")
		#Heading - True
		self.NMEASyntax["HDT"] = ("headingTrueDegrees", "true")
		#Own ship data
		self.NMEASyntax["OSD"] = ("headingTrueDegrees", "status", "courseTrueDegrees", "courseReference", "speed", "speedReference", "vesselSetTrueDegrees", "vesselDrift", "speedUnit")
		#True heading and status
		self.NMEASyntax["THS"] = ("headingTrueDegrees", "faaModeIndicator")
		#Water speed and heading
		self.NMEASyntax["VHW"] = ("headingWaterTrueDegrees", "true", "headingWaterMagneticDegrees", "magnetic", "speedOverWaterKnots", "knots", "speedOverWaterKph", "kph")
		#Geographic position - Lat/Lon data
		self.NMEASyntax["GLL"] = ("latitude", "northSouth", "longitude", "eastWest", "timeHMS", "status", "faaModeIndicator")
		#Datum reference
		self.NMEASyntax["DTM"] = ("localDatum", "localDatumSub", "latitudeOffsetMinutes", "northSouth", "longitudeOffsetMinutes", "eastWest", "altitudeOffsetMeter", "datumName")
		#GNSS satellites in view
		#self.NMEASyntax["GSV"] = ("numberOfGSVMessages", "messageNumber", "numberOfSatsInView", "satPRNNumber1", "satElevationDegrees1", "satAzimuthTrueNorthDegrees1", "satSNRdB1", "satPRNNumber2", "satElevationDegrees2", "satAzimuthTrueNorthDegrees2", "satSNRdB2", "satPRNNumber3", "satElevationDegrees3", "satAzimuthTrueNorthDegrees3", "satSNRdB3", "satPRNNumber4", "satElevationDegrees4", "satAzimuthTrueNorthDegrees4", "satSNRdB4")
		#Rate of turn
		self.NMEASyntax["ROT"] = ("rateOfTurnDegreesInMinute", "status")
		#Revolutions
		self.NMEASyntax["RPM"] = ("revolutionsSource", "engineShaftNumber", "revolutionsRPM", "propellerPitch", "status")
		#Rudder sensor angle
		self.NMEASyntax["RSA"] = ("rudderStarboardSensor", "status", "rudderPortSensor", "status")
		#GPS Fix data
		self.NMEASyntax["GGA"] = ("timeHMS", "latitude", "northSouth", "longitude", "eastWest", "gpsQualityIndicator", "numberOfSatsInUse", "horizontalDillutionMeter", "antennaAltitudeSeaLevelMeter", "meter", "geoidalSeparationMeter", "meter", "dgpsAge", "dgpsStationID")
		#Recommended minimum specific GNSS data
		self.NMEASyntax["RMC"] = ("timeHMS", "status", "latitude", "northSouth", "longitude", "eastWest", "speedOverGroundKnots", "trackMadeGoodTrueDegrees", "dateDDMMYY", "magneticVariationDegrees", "magneticVariationDirection")
		#Time and date
		self.NMEASyntax["ZDA"] = ("timeHMS", "day", "month", "year", "localTimeZoneDescriptionHours", "localTimeZoneDescriptionMinutes")
		#Water temperature
		self.NMEASyntax["MTW"] = ("waterTemperatureCelcius", "celcius")
		#Wind speed and angle
		self.NMEASyntax["MWV"] = ("windAngleDegrees", "windAngleReference", "windSpeed", "windSpeedUnit", "status")
		#Wind Direction and speed
		self.NMEASyntax["MWD"] = ("windAngleTrueDegrees", "true", "windAngleMagneticDegrees", "magnetic", "windSpeedKnots", "knots", "windSpeedMeter", "meter")



	def parse(self):
		#regex funds udp header part and nmea_0184 part. It returns the vallues in groups
		# regex = r"(?#IEC 61162-450 HEADER)(?:(?#HEADER)(?P<header>(UdPbC(?:\0)?)){1}(?#ENDHEADER)(?#TAG)\\(?P<tag>(?:(?#Source)(?:s:(?P<source>[0-9a-zA-Z]*)(?:[,|\*]){1}){1}(?#endsource)|(?#linenumber)(?:n:(?P<lineNumber>[0-9]*)(?:[,|\*]){1}){1}(?#endlinenumber)|(?#destination)(?:d:(?P<destination>[0-9a-zA-Z]*)(?:[,|\*]){1}){1}(?#enddestination)|(?#unsupportedTag)(?:\w:(?P<unSupportedTag>[0-9a-zA-Z]*)(?:[,|\*]){1}){1}(?#endunsupportedTag))*)(?P<tagChecksum>[0-9a-zA-Z]{2})\\(?#ENDTAG))?(?#ENDOF IEC61162-450 HEADER)(?#NMEASENTENCE)\$(?P<talkerID>[a-zA-Z]{2})(?P<sentenceID>[a-zA-Z]{3}),(?P<data>.*)\*(?P<checksum>[0-9a-zA-Z]{2})(?#ENDNMEASENTENCE)"
		regex = r"(?#IEC 61162-450 HEADER)((?#TAG)\\(?P<tag>((?#Source)(s:(?P<source>[0-9a-zA-Z]*)([,|\*]){1}){1}(?#endsource)|(?#linenumber)(n:(?P<lineNumber>[0-9]*)([,|\*]){1}){1}(?#endlinenumber)|(?#destination)(d:(?P<destination>[0-9a-zA-Z]*)([,|\*]){1}){1}(?#enddestination)|(?#unsupportedTag)(\w:(?P<unSupportedTag>[0-9a-zA-Z]*)([,|\*]){1}){1}(?#endunsupportedTag))*)(?P<tagChecksum>[0-9a-zA-Z]{2})\\(?#ENDTAG))?(?#ENDOF IEC61162-450 HEADER)(?#NMEASENTENCE)\$(?P<talkerID>[a-zA-Z]{2})(?P<sentenceID>[a-zA-Z]{3}),(?P<data>.*)\*(?P<checksum>[0-9a-zA-Z]{2})(?#ENDNMEASENTENCE)"
		matches = re.finditer(regex, self.nmeaString)
                resultDict = {}

		reTag = None
		nmeaDict = {}
		finalNmeaDict = {}
		if self.nmeaString.startswith('UdPbC'):#\x00'):
			reHeader = 'UdPbC'
		for matchNum, match in enumerate(matches):
			nmeaDict[matchNum] = {}
			nmeaDict[matchNum]["reTag"] 			= 	self.ReturnRegexGroup(match,"tag").replace("*","")
			nmeaDict[matchNum]["reSource"] 		= 	self.ReturnRegexGroup(match,"source")
			nmeaDict[matchNum]["reLineNumber"] 	= 	self.ReturnRegexGroup(match,"lineNumber")
			nmeaDict[matchNum]["reUnSupportedTag"]= 	self.ReturnRegexGroup(match,"unSupportedTag")
			nmeaDict[matchNum]["reTagChecksum"] 	= 	self.ReturnRegexGroup(match,"tagChecksum")
			nmeaDict[matchNum]["reTalkerID"] 		= 	self.ReturnRegexGroup(match,"talkerID")
			nmeaDict[matchNum]["reSentenceID"] 	= 	self.ReturnRegexGroup(match,"sentenceID")
			nmeaDict[matchNum]["reData"] 			= 	self.ReturnRegexGroup(match,"data")
			nmeaDict[matchNum]["reChecksum"]		=	self.ReturnRegexGroup(match,"checksum")

		# 	print "Tag = " + str(nmeaDict[matchNum]["reTag"])
		# 	print "source = " + str(nmeaDict[matchNum]["reSource"])
		# 	print "lineNumber = " + str(nmeaDict[matchNum]["reLineNumber"])
		# 	print "unSupportedTag = " + str(nmeaDict[matchNum]["reUnSupportedTag"])
		# 	print "tagChecksum = " + str(nmeaDict[matchNum]["reTagChecksum"])
		# 	print "talkerID = " + str(nmeaDict[matchNum]["reTalkerID"])
		# 	print "sentenceID = " + str(nmeaDict[matchNum]["reSentenceID"])
		# 	print "data = " + str(nmeaDict[matchNum]["reData"])
		# 	print "checksum = " + str(nmeaDict[matchNum]["reChecksum"])
		# 	print "---------------------------------------"
		# print "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-++-+-+-+-"

		#perform some checks to see if the data is valid
		for line in nmeaDict:
                       try:
			if nmeaDict[line]["reTag"] != None:
				if not self.checksumCheck(checksumSentence = nmeaDict[line]["reTag"], checksum = nmeaDict[line]["reTagChecksum"]):
					continue
			if (self.talkerID != None) and  (self.talkerID != nmeaDict[line]["reTalkerID"]):
				continue
			if (self.identifier != None) and  (self.identifier != nmeaDict[line]["reSentenceID"]):
				continue
			if not self.checksumCheck(checksumSentence = nmeaDict[line]["reTalkerID"] + nmeaDict[line]["reSentenceID"] + "," + nmeaDict[line]["reData"], checksum = nmeaDict[line]["reChecksum"]):
				continue
			#split the data of the nmea syntax as these are comma seperated
			nmeaParts = nmeaDict[line]["reData"].split(",")
			#if there is a reSource, the data is UDP else we use reTalkerID for old NMEA format
			ID = nmeaDict[line]["reSource"] if (nmeaDict[line]["reSource"] != None) else nmeaDict[line]["reTalkerID"]

			#initialize variables
			if not ID in finalNmeaDict:
				finalNmeaDict[ID] = {}
			i = 0
			#if the nmea syntax is know, we use the list initialized on top of program
			if nmeaDict[line]["reSentenceID"] in self.NMEASyntax:
				for part in nmeaParts:
					if part != "":
						finalNmeaDict[ID][self.NMEASyntax[nmeaDict[line]["reSentenceID"]][i]] = part
					i += 1
			#if we do not know the nmea format, we return the index of the comma seperated field
			else:
				for part in nmeaParts:
					if part != "":
						finalNmeaDict[ID][nmeaDict[line]["reSentenceID"] + "_" + str(i)] = part
					i += 1
			#we insert the original SentenceID in the return value dictionary
			#finalNmeaDict[ID][nmeaDict[line]["reSentenceID"]] = True
                        resultDict = {}
                        resultDict[ID] = {}   
                        #print (nmeaDict[line]["reSentenceID"])
                        resultDict[ID][nmeaDict[line]["reSentenceID"]] = finalNmeaDict[ID]
                       except Exception as e: 
                        print e
		#import pprint
		#pprint.pprint(resultDict)
		# return None
		#return finalNmeaDict
                return resultDict





	def checksumCheck(self,checksumSentence = None, checksum = None):
		#returns True if correct
		if (checksumSentence == None) or (checksum == None) :
			return False

		calcChecksum = 0
		for char in checksumSentence:
			calcChecksum ^= ord(char)
		if not hex(calcChecksum) == hex(int(checksum,16)):
			return False
		return True

	def ReturnRegexGroup(self,match,groupname):
		#returns the regex group vallue if exist. Else it returns None
		try:
			result = match.group(groupname)
			return result
		except:
			return None



