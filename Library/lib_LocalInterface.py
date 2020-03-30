"""
	Functions that have something todo with the local interface
"""

import fcntl, socket,struct
import lib_MAC

class LocalInterface(object):
	def __init__(self, interfaceName):
		self.interfaceName = interfaceName
		return

	def getLocalInterfaceHwAddr(self):
		"Returns MAC-address of given interface"
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', self.interfaceName[:15]))
		hwaddr = str(':'.join(['%02x' % ord(char) for char in info[18:24]]))
		return lib_MAC.MAC.ConvertMACToStandardFormat(hwaddr)

def ReadBandwith (**kwargs):

	datatypes = kwargs.pop('datatypes',None)
	interfaces = kwargs.pop('interfaces',None)
	if (datatypes == None) or (interfaces == None):
		return None 
	if not isinstance(datatypes, (list,tuple)):
		datatypes = (datatypes,)
	if not isinstance(interfaces, (list,tuple)):
		interfaces = (interfaces,)
	result = {}
	for interface in interfaces:
		if not interface in result:
			result[interface] = {}
		for data in datatypes:
			# if not data in result[interface]:
			# 	result[interface][data] = {}
			try:
				file = open("/sys/class/net/" + interface + "/statistics/" + data, "r")
				result[interface][data] = file.read().strip()
				file.close()
			except:
				result[interface][data] = None
	return result