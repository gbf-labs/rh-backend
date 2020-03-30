"""
	Functions that have something todo with MAC-addresses
"""


class MAC(object):

	@classmethod #global class method
	def ConvertMACToStandardFormat(cls,MacAddress):
		"Convert Mac to Standard Format (aa:bb:cc:dd:ee:ff)"
		MacAddress = MacAddress.replace(":","").lower()
		MacAddress = MacAddress.replace(".","").lower()
		MacAddress = MacAddress.replace("-","").lower()
		if "error" in MacAddress:
			MacAddress = MacAddress.upper()
		elif not len(MacAddress) == 12:
			MacAddress = "ERROR (" + MacAddress + ")"
		else:
			MacAddress =  MacAddress[0:2] + ":" + MacAddress[2:4] + ":" + MacAddress[4:6] + ":" + MacAddress[6:8]+ ":" + MacAddress[8:10] + ":" + MacAddress[10:12]
		return MacAddress

	@classmethod #global class method
	def ConvertMACToCiscoFormat(cls,MacAddress):
		"Convert Mac to Cisco Format (aabb.ccdd.eeff)"
		MacAddress = MacAddress.replace(".","").lower()
		MacAddress = MacAddress.replace("-","").lower()
		MacAddress = MacAddress.replace(":","").lower()
		if "error" in MacAddress:
			MacAddress = MacAddress.upper()
			pass
		elif not len(MacAddress) == 12:
			MacAddress = "ERROR (" + MacAddress + ")"
		else:		
			MacAddress = MacAddress[0:4] + "." + MacAddress[4:8] + "." + MacAddress[8:12]
		return MacAddress

	def __init__(self,address):
		self.address = MAC.ConvertMACToStandardFormat(address)		
		return

	def GetMACInCiscoFormat(self):
		return MAC.ConvertMACToCiscoFormat(self.address)

	def GetMACInStandardFormat(self): #same as MAC.address
		return self.address

