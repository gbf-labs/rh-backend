import urllib2
from bs4 import BeautifulSoup
import lib_Log
import requests
import lib_ICMP
import re
import ssl
from requests.auth import HTTPDigestAuth

class WebScraping(object):
    def __init__(self):
        self.log = lib_Log.Log(PrintToConsole=True)
        self.Error = False
        self.soup = ""
        self.log.increaseLevel()

    def URL(self,URL):

        if self.Error == False:
            IP = re.findall("\/\/([^\/]+)\/",URL)[0]
            IP = IP.split(':')[0]
            PING = lib_ICMP.Ping(IP)

            if PING.DoPingTest():
                self.log.printInfo("Successfully Reached %s"%IP)
            else:
                self.log.printWarning("Can Not Reach %s" % IP)
                self.Error = True

        if self.Error == False:   
            try:    
                if URL.lower().startswith("https"):
                    context = ssl._create_unverified_context()
                    page = urllib2.urlopen(URL, timeout = 10, context = context)
                else:
                    page = urllib2.urlopen(URL,timeout = 10)
                self.soup = BeautifulSoup(page,"html.parser")
            except Exception as e:
                self.Error = True
                self.log.printError(e)

    def URLWithAuthenticate(self,Username,Password,URL):

        if self.Error == False:
            IP = re.findall("\/\/([^\/]+)\/",URL)[0]
            IP = IP.split(':')[0]
            PING = lib_ICMP.Ping(IP)
            if PING.DoPingTest():
                self.log.printInfo("Successfully Reached %s"%IP)
            else:
                self.log.printWarning("Can Not Reach %s" % IP)
                self.Error = True

        if self.Error == False:  
            try:                 
                data = requests.get(URL, auth=HTTPDigestAuth(Username, Password),timeout = 10)
                self.soup = BeautifulSoup(data.content,"html.parser")

            except Exception as e:
                self.soup = ""

    def FindStringInTagWithKey(self,Tag = "",Keyname = "id", KeyValue = "", Attribute = None , data = None):
        if self.Error == False:
            if data == None:
                data = self.soup
            try:
                Key = {Keyname : KeyValue}
                if Attribute != None:
                    data = data.find( Tag, Key )[Attribute]
                else:
                    data = data.find( Tag, Key).string

                return (str(data)).replace('\n', '').replace('\r', '')
            except:
                if Attribute != None:
                    Attribute = ",Attribute " + Attribute
                else:
                    Attribute = ""
                self.log.printWarning("Can Not find Tag %s, %s:%s Atribute %s" % (Tag,Keyname,KeyValue,Attribute))
                return None
        return None

    
    def DeepTagSearch(self,**kwargs):
    
        tagList = kwargs.pop('tagList',None)
        if tagList == None:
            return None
        if not isinstance(tagList, (list,tuple)):
            tagList = (tagList,)
        result = kwargs.pop('data',self.soup)

        try:
            for tag in tagList:
                result = result.find(tag)
        except:
            result = None
        return result