"""
        Functions that have something todo with ICMP (e.g. Ping)
"""
import os, platform
import subprocess
import time
import parse
import lib_Bash

class Ping(object):
    def __init__(self, IP):
        self.IP = IP
                
    def GetPingSuccessrate(self,pingAmount = 5,interface = None):
        counter = 0
        successcount = 0
        while counter < pingAmount:
            if self.DoPingTest(interface = interface):
                successcount += 1
            counter += 1
        return (successcount / float(pingAmount))


    def DoPingTest(self,interface = None):
        Inf = ""
        if interface != None:
            Inf = "-I " + interface + " "
        if lib_Bash.Bash("ping " + Inf + "-c 1 " + self.IP):
            is_up = False
        else:
            is_up = True
                
        return is_up        
                    

    def DoPingTestExtended(self):
        """
        returns array
                ["error" => true | false]
                ["errormsg" => "" | <ErrorMsg>]
                ["bytes" => ""]
                ["ip"    => ""]
                ...

        """
        returnValue = {}

        #p = subprocess.Popen(['ls', '-a'], stdout=subprocess.PIPE,
        #                                  stderr=subprocess.PIPE)

        p = subprocess.Popen(['ping', '-n', '-c' , '1', self.IP], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        out, err = p.communicate()
        returnValue["error"] = True
        returnValue["timestamp"] = time.time()
        returnValue = {}

        out = out.decode('ascii')
        err = err.decode('ascii')
        if (err == ""):
            i = 0
            for line in out.split('\n'):  #run over each line in out
                i += 1
                if (i == 2): #only check second line
                    parsed = parse.parse("{bytes} bytes from {ip}: icmp_seq={seq} ttl={ttl} time={time} ms", line)

                    if parsed is None:
                        returnValue['dest'] = self.IP
                        returnValue["error"] = True
                        returnValue["errormsg"] = "No respons"
                    else:
                        try:
                            returnValue['error'] = True #set first to false so if try fails we have a false
                            returnValue['errormsg'] = ""
                            returnValue['dest'] = self.IP
                            returnValue['bytes'] = parsed['bytes']
                            returnValue['ip'] = parsed['ip']
                            returnValue['seq'] = parsed['seq']
                            returnValue['ttl'] = parsed['ttl']
                            returnValue['time'] = parsed['time']
                            returnValue["errormsg"] = ""
                            returnValue["error"] = False
                        except:
                            returnValue['dest'] = self.IP
                            returnValue["error"] = True
                            returnValue["errormsg"] = err
                            returnValue['bytes'] = None
                            returnValue['ip'] = None
                            returnValue['seq'] = None
                            returnValue['ttl'] = None
                            returnValue['time'] = None
                            pass
        else:
            returnValue['dest'] = self.IP
            returnValue["error"] = True
            returnValue["errormsg"] = err

        return returnValue

    def DoTraceroute(self,Hops = 2):
        """
        returns array
                ["error" => true | false]
                ["errormsg" => "" | <ErrorMsg>]
                ["bytes" => ""]
                ["ip"    => ""]
                ...

        """
        #p = subprocess.Popen(['ls', '-a'], stdout=subprocess.PIPE,
        #                                  stderr=subprocess.PIPE)

        p = subprocess.Popen(["traceroute", self.IP, "-I","-m", str(Hops),"-q","1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        returnValue = {}

        if (err == ""):

            for line in out.split('\n'):  #run over each line in out
                parsed = parse.parse("{hop} {DNS} ({IP}) {time} ms", line)

                if parsed is not None:
                    returnValue[parsed['hop']] = {}
                    returnValue[parsed['hop']]["DNS"] = parsed['DNS']
                    returnValue[parsed['hop']]["IP"] = parsed['IP']
                    returnValue[parsed['hop']]["TIME"] = parsed['time']
        else:
            return None

        return returnValue