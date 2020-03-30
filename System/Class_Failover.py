import netifaces
import time
import sys
import os
import lib_Bash
import lib_Mail
import lib_Log
# import lib_SQLdb
import lib_CouchDB
import lib_ICMP
import lib_LocalInterface
import ConfigParser
import copy
import pprint
import threading
import lib_config


class Failover(object):



        def __init__(self,INI):                
                self.log = lib_Log.Log(PrintToConsole=True)
                self.Error = False
                self.INI = INI
                self.ReadError = False
                self.Renew = False
                self.ClearFailoverVariables()
                self.ServerIP = "185.95.73.13"
                self.ServerVPNIP = "185.95.73.13"
                self.Ping = lib_ICMP.Ping(self.ServerIP)
                self.PingVPN = lib_ICMP.Ping(self.ServerVPNIP)

                self.StandardDefaultGW = self.GetDefaultGateway()

                #create variables for priorities (datacounter)
                self.CounterDatatypes = ("rx_bytes","tx_bytes")
                self.CounterInterfaces = "tun1"
                temp = lib_LocalInterface.ReadBandwith(datatypes = self.CounterDatatypes, interfaces = self.CounterInterfaces)
                self.rxBytes = temp["tun1"]["rx_bytes"]
                self.txBytes = temp["tun1"]["tx_bytes"]
                self.MailInternalSend = False
                self.MailExternalSend = False
                ExternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","EXTERNALMAILDELAY")
                if ExternalMailDelay is None:
                        #if no delay is set, we set to 30 min
                        ExternalMailDelay = 60 * 30
                        self.log.printWarning("ExternalMailDelay not defined in ini-file, set to %s seconds" % ExternalMailDelay)
                InternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","INTERNALMAILDELAY")
                if InternalMailDelay is None:
                        #if no delay is set, we set to 15 min
                        InternalMailDelay = 60 * 15
                        self.log.printWarning("InternalMailDelay not defined in ini-file, set to %s seconds" % InternalMailDelay)
                self.ExternalMailDelay = ExternalMailDelay
                self.InternalMailDelay = InternalMailDelay
                self.ExternalMailSend = False
                self.InternalMailSend = False
                self.ChangedInterfaceTime = None
                self.InterfaceBeforeLastMail = None
                self.LastSuccessVPNPing = time.time()
                #how long does an iterface deserves to be "burned" before we can use it again (seconds)
                self.InterfaceBurnRestoreTime = 60 * 10
                #after how long with unsuccessfull vpn pings an interface becomes "burned"
                self.InterfaceBurnTime = 60 * 1
                #initialize time of burn to now, so counter starts here
                self.InterfaceBurningTime = time.time()
                self.BurnedInterface = None
                #checktimes is used for how often we need to check some parameters
                self.checktime = time.time()


                #create SQL instance
                # self.sql = lib_SQLdb.Database()
                self.couch_db = lib_CouchDB.COUCH_DATABASE()

                config_data = lib_config.CONFIG_DATA()
                
                self.config_interface = config_data.interface

        def ManualGateway(self,**kwargs):
                self.log.printInfo ("Start Failover Manipulation")
                file = "/home/rh/backendv1/ini/EMGFAILOVER.INI"
                RemoteCommand = kwargs.pop('RemoteCommand',None)
                failoverSection = RemoteCommand.pop('Device',None)
                option = RemoteCommand.pop('Option', None)
                if option != None:
                        option.lower()
                if failoverSection != None:
                        failoverSection.lower()
                if option == "reset" and failoverSection == "ALL":
                        open(file, 'w').close()
                        self.log.printOK("All failover manipulations successfully removed")
                        return 


                config = ConfigParser.ConfigParser()
                config.read(file)
                #reset if option tells so
                if option == "reset":
                        if config.has_section(failoverSection):
                                config.remove_section(failoverSection)
                                with open(file, 'wb') as configfile:
                                        config.write(configfile)
                        self.log.printOK("failover manipulations for %s successfully removed" % failoverSection)
                        return
                #remove already existing force rules. There can be only one
                if option == "force":
                        sections = config.sections()
                        for section in sections:
                                if config.has_option(section,"rule"):
                                        if config.get(section, "rule") == "force":
                                                config.remove_option(section, "rule")
                                                self.log.printWarning("Removed Previous forcing for %s as there can only be one forcing at a time" % section)

                if not config.has_section(failoverSection):
                        config.add_section(failoverSection)
                config.set(failoverSection, "rule", option)

                with open(file, 'wb') as configfile:
                        config.write(configfile)
                self.log.printOK("%s rule successfully applied for %s" % (option, failoverSection))


        def AutoGateway(self):
                #set the DNS servers in /etc/resolv.conf
                DNS = ["8.8.8.8","8.8.4.4"]
                self.SetDNS(DNS)
                #write to log
                self.log.printBoldInfo("Failover Mechanism")
                self.log.increaseLevel()
                #get list of existing priority's in ordered fomralt ex: [1,2,6,10] and exit if None
                self.Priorities = self.GetFailoverPriorities()
                if self.Priorities == None or self.Priorities == []:
                        self.log.printError("No Failover Priorities known")
                        return
                #start own Failover system
                self.OwnFailover()


        def ExternalFailover(self):
                CurrentInterface = None
                #tracert = lib_ICMP.Ping("8.8.8.8")
                tracert = lib_ICMP.Ping(self.ServerIP)
                #create SQL instance
                # sql = lib_SQLdb.Database()
                #set all counter to NOW (Zero)
                MaxHops = self.INI.getOptionInt("FAILOVERGENERAL","MAXHOPS")
                if MaxHops == None:
                        self.log.printWarning("Amount of MaxHops not defined in INI, MaxHops is set to 5 by default")
                        MaxHops = 5
                Gateway = None
                interface = None
                Description = None
                result = {}
                result["Gateway"] = Gateway
                TweenTime = time.time()   
                mainLoopTime    = self.INI.getOptionInt("MAIN_PROGRAM","MAINLOOPTIME")
                if mainLoopTime is None:
                        mainLoopTime = 60 * 10
                        self.log.printWarning("Main loop time time not defined in ini-file, set to %s seconds" % mainLoopTime)

                while True:
                        try:
                                #Renew info when Main reInitializes ini and sets self.Renew
                                if self.Renew:
                                        CurrentInterface = None
                                        Gateway = None
                                        interface = None
                                        Priority = None
                                        Description = None
                                        self.Policy = None
                                        self.Renew = False
                                        MaxHops = self.INI.getOptionInt("FAILOVERGENERAL","MAXHOPS")
                                        if MaxHops == None:
                                                MaxHops = 5
                                        ExternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","EXTERNALMAILDELAY")
                                        if ExternalMailDelay is None:
                                                #if no delay is set, we set to 30 min
                                                ExternalMailDelay = 60 * 30
                                                self.log.printWarning("ExternalMailDelay not defined in ini-file, set to %s seconds" % ExternalMailDelay)
                                        InternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","EXTERNALMAILDELAY")
                                        if InternalMailDelay is None:
                                                #if no delay is set, we set to 15 min
                                                InternalMailDelay = 60 * 15
                                                self.log.printWarning("InternalMailDelay not defined in ini-file, set to %s seconds" % InternalMailDelay)
                                        self.ExternalMailDelay = ExternalMailDelay
                                        self.InternalMailDelay = InternalMailDelay



                                #Every looptime, confirm all  data to SQL
                                if (time.time() - TweenTime) >= mainLoopTime:
                                        TweenTime = time.time()
                                        result = {}
                                        result["Description"] = Description
                                        result["Gateway"] = Gateway
                                        result["Interface"] = interface
                                        result["Policy"] = self.Policy
                                        result["Failover"] = Priority
                                        result.update(self.GetCounters())
                                        #create tables, fill tables
                                        paramArray = {}
                                        paramArray["FAILOVER"] = {}
                                        paramArray["FAILOVER"][0] = {}
                                        paramArray["FAILOVER"][0]["General"] = result
                                        paramArray["FAILOVER"][0]["_ExtractInfo"] = {}
                                        paramArray["FAILOVER"][0]["_ExtractInfo"]["ExtractTime"] = time.time()
                                        
                                        print "1============================================="
                                        print "Class_Failover"
                                        print "1============================================="
                                        # sql.WriteArrayData(self.INI,paramArray,uniqueTable = "failover")
                                        self.couch_db.write_default_values(self.INI, paramArray, uniqueTable = "failover")
                                        print "1============================================="
                                        print "END"
                                        print "1============================================="
                                

                                Hop=1
                                Continue = True
                                while Continue:
                                        if Hop > MaxHops:
                                                self.log.printWarning("MaxHops '%s' is reached without resolving a known/defined gateway")
                                                Hop = 1
                                        traceresult = tracert.DoTraceroute(Hops = Hop)
                                        Hop += 1
                                        if traceresult != None:
                                                Gateway = traceresult[max(traceresult)]["IP"]
                                                KnownGateway = False
                                                for a in Priorities:
                                                        if Gateway == self.INI.getOptionStr("FAILOVER",a,"GATEWAY"):
                                                                Description = self.INI.getOptionStr("FAILOVER",a,"DESCRIPTION")
                                                                self.Policy = self.INI.getOptionStr("FAILOVER",a,"POLICY")
                                                                interface = self.INI.getOptionStr("FAILOVER",a,"INTERFACE")
                                                                Priority = "FAILOVER" + str(a)
                                                                Continue = False
                                                                KnownGateway = True
                                                                break

                                                if Gateway != result["Gateway"] and KnownGateway == True:
                                                        if a == min(Priorities) and result["Gateway"] == None:
                                                                Message = "System went to Preferred Network '%s' at STARTUP" % Description
                                                                self.log.printOK(Message)
                                                        else:
                                                                if a == min(Priorities):
                                                                        Message = "System returned to preferred Network '%s'" % Description                 
                                                                else:
                                                                        Message = "Failover switched to '%s'. This profile has priority %s. \n"%(Description,a)
                                                                        Message += "\nYour prefered profile '%s' has no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",min(Priorities),"DESCRIPTION"))
                                                                        for backup in Priorities:
                                                                                if backup != min(Priorities) and backup < a:
                                                                                        Message += "Profile '%s' with priority %s, has also no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",backup,"DESCRIPTION"),backup) 
                                                                        Message += "\nPlease be aware of the change as it may result in expencive connectivity bills.\n"

                                                                Message += "\n\nThis is an autogenerated Message, pls do not reply!\n"
                                                                Message += "\n\nBest Regards, \nRHBOX-Team"
                                                                Message += "\n\n--------------------------------------------------"
                                                                Message += "\nMailTimestamp: " + str(time.strftime("%Y-%m-%d %H:%M:%S")) + " UTC"


                                                                #print Message
                                                                Mail = lib_Mail.Mail(self.INI,"FAILOVERGENERAL")
                                                                Mail.Set_Subject("Failover Event,  %s   IMO: %s   MMSI: %s" % (self.INI.getOptionStr("INFO","VESSELNAME"),self.INI.getOptionStr("INFO","IMO"),self.INI.getOptionStr("INFO","MMSI")))
                                                                Mail.Set_Message(Message)
                                                                #Mail.Set_Attachement("/rhbox/log/","VSATBOX.log")
                                                                Mail.Send_Mail()
                                                                del Mail

                                                        #write the results into Database
                                                        TweenTime = time.time()
                                                        result = {}
                                                        result["Description"] = Description
                                                        result["Gateway"] = Gateway
                                                        result["Interface"] = interface
                                                        result["Policy"] = self.Policy
                                                        result["Failover"] = Priority
                                                        result.update(self.GetCounters())
                                                        self.log.printInfo("Failover set to '%s' GW '%s' IF '%s' with Policy '%s'"% (Description,Gateway,interface,self.Policy))
                                                        #create tables, fill tables
                                                        paramArray = {}
                                                        paramArray["FAILOVER"] = {}
                                                        paramArray["FAILOVER"][0] = {}
                                                        paramArray["FAILOVER"][0]["General"] = result
                                                        paramArray["FAILOVER"][0]["_ExtractInfo"] = {}
                                                        paramArray["FAILOVER"][0]["_ExtractInfo"]["ExtractTime"] = time.time()
                                                        
                                                        print "2============================================="
                                                        print "Class_Failover"
                                                        print "2============================================="
                                                        # sql.WriteArrayData(self.INI,paramArray,uniqueTable = "failover")
                                                        self.couch_db.write_default_values(self.INI, paramArray, uniqueTable = "failover")
                                                        print "2============================================="
                                                        print "END"
                                                        print "2============================================="
                                #wait time between ping tries
                                time.sleep(10)

                        except KeyboardInterrupt:
                                self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                                exit()
                        except Exception as e:
                                pass

        def OwnFailover(self):
                #Remove old and set the new Gateways with metric. Included DHCP with metric 100
                self.SetInitalGateways(StartMetric = 10)
                #initialize
                self.TweenTime = time.time()   
                mainLoopTime    = self.INI.getOptionInt("MAIN_PROGRAM","MAINLOOPTIME")
                if mainLoopTime is None:
                        mainLoopTime = 60 * 10
                        self.log.printWarning("Main loop time time not defined in ini-file, set to %s seconds" % mainLoopTime)
                #Create ping instance towards VPN server
                Ping = lib_ICMP.Ping(self.ServerIP)
                self.Policy = None                
                
                #forever loop
                while True:
                        try:
                                #make sure failover is not taking all recources from processor
                                time.sleep(2)
                                #Renew info when Main reInitializes ini and sets self.Renew or on first run
                                if self.Renew:
                                        self.log.printInfo("Reloading Failover Parameters dus to INI files updates")
                                        self.Priorities = self.GetFailoverPriorities()
                                        #Remove old and set the new Gateways with metric. Included DHCP with metric 100
                                        self.SetInitalGateways(StartMetric = 10)
                                        #set all counter to NOW (Zero)
                                        self.ClearFailoverVariables()
                                        self.interface = None

                                        self.TweenTime = time.time()   
                                        mainLoopTime    = self.INI.getOptionInt("MAIN_PROGRAM","MAINLOOPTIME")
                                        if mainLoopTime is None:
                                                mainLoopTime = 60 * 10
                                                self.log.printWarning("Main loop time time not defined in ini-file, set to %s seconds" % mainLoopTime)
                                        ExternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","EXTERNALMAILDELAY")
                                        if ExternalMailDelay is None:
                                                #if no delay is set, we set to 15 min
                                                ExternalMailDelay = 60 * 15
                                                self.log.printWarning("ExternalMailDelay not defined in ini-file, set to %s seconds" % ExternalMailDelay)
                                        InternalMailDelay    = self.INI.getOptionInt("FAILOVERGENERAL","EXTERNALMAILDELAY")
                                        if InternalMailDelay is None:
                                                #if no delay is set, we set to 25 min
                                                InternalMailDelay = 60 * 25
                                                self.log.printWarning("InternalMailDelay not defined in ini-file, set to %s seconds" % InternalMailDelay)
                                        self.ExternalMailDelay = ExternalMailDelay
                                        self.InternalMailDelay = InternalMailDelay
                                        self.ExternalMailSend = False
                                        self.InternalMailSend = False
                                        self.ChangedInterfaceTime = None
                                        self.Renew = False

                                #Every looptime, confirm all  data to SQL
                                if (time.time() - self.TweenTime) >= mainLoopTime:
                                        #writing to database
                                        self.WriteToDatabase()
                                        self.TweenTime = time.time()

                                #check all every 5 sec
                                if ((self.checktime + 10) < time.time()):
                                        self.checktime = time.time()
                                        #check if mailsend is required
                                        self.SendMailIfRequired()

                                        #check if VPN is UP
                                        self.CheckVPN()
                                
                                for a in self.Priorities:
                                        testInterface = self.INI.getOptionStr("FAILOVER",a,"INTERFACE")
                                        # print "testinterface = %s" % testInterface
                                        if ((testInterface != None) and (self.BurnedInterface != testInterface)):
                                                retry = 0
                                                pingtime = time.time()
                                                while retry < 5:
                                                        if time.time() > (pingtime + 10) :
                                                                pingtime = time.time()
                                                                # print "retry = %s" % retry
                                                                # print "failover alive"
                                                                # print "ping %s" % testInterface
                                                                # print "\n"
                                                                #wait time between ping tries
                                                                # time.sleep(10)
                                                                #get average success ping result and if better than 60% continue (3 out of 5)
                                                                successRate = Ping.GetPingSuccessrate(pingAmount = 5,interface = testInterface)
                                                                # print "successRate = %s" % successRate
                                                                if successRate >= 0.6:
                                                                        #if this is priority 1 at boot 
                                                                        if self.interface == None and a == min(self.Priorities):
                                                                                self.ReplaceMainGateway(FailoverNumber = a)
                                                                                # no mail send is required, but print to log is
                                                                                self.log.printOK("System went to Preferred Network '%s' at STARTUP" % self.Description)
                                                                        elif testInterface != self.interface:
                                                                                #change inteface and store values
                                                                                self.ReplaceMainGateway(FailoverNumber = a)
                                                                                #prepare message for mail and write to log
                                                                                self.SetMessageChangeInterface(FailoverNumber = a)
                                                                        else:
                                                                                pass
                                                                                #self.log.printInfo("Interface %s was already set as Default Gateway"% self.interface)
                                                                                print ("Interface %s was already set as Default Gateway" % self.interface)
                                                                        raise ValueError("restart ping cycle")
                                                                else:
                                                                        pass
                                                                        #self.log.printError("Ping via %s Failed" % self.interface)
                                                                        #print "Ping via %s Failed" % self.interface
                                                                retry = retry + 1
                                                        else:
                                                                time.sleep(1)

                                #if program gets here, the default interface could not be set.
                                #We can try to go to the default gateway given by the dhcp lease
                                if self.StandardDefaultGW != None:
                                        testInterface = self.config_interface
                                        # print "testinterface = %s" % testInterface
                                        retry = 0
                                        while retry < 5:
                                                #wait time between ping tries
                                                if time.time() > (pingtime + 10) :
                                                                pingtime = time.time()
                                                                # print "retry = %s" % retry
                                                                retry = retry + 1
                                                                #get average success ping result and if better than 60% continue (3 out of 5)
                                                                if Ping.GetPingSuccessrate(pingAmount = 5,interface = testInterface) >= 0.6:
                                                                        if testInterface != self.interface:
                                                                                self.ReplaceMainGateway(DHCP = True)
                                                                                self.SetMessageChangeInterface(DHCP = True)                
                                                                                raise ValueError("restart ping cycle")
                        except KeyboardInterrupt:
                                self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                                exit()
                        except Exception as e:
                                # print "error"
                                # print e
                                # print "\n"
                                pass

                                                                        



        def GetPriorityByGateway(self,Gateway):
                #serach for existing Failover
                Failover = self.INI.getOption("FAILOVER")
                if Failover is None:
                        return None
                Priorities = []
                for devNumber in Failover:
                        if "GATEWAY" in  Failover[devNumber]:
                                if Failover[devNumber]["GATEWAY"] == Gateway:
                                        return devNumber


        def GetDefaultGateway(self):
                try:   
                        CurrentDefaultGW = str(netifaces.gateways()["default"][netifaces.AF_INET][0])
                except:
                        CurrentDefaultGW = None
                return CurrentDefaultGW


        def SetInitalGateways(self,StartMetric = 10):
                self.DelAllGateways()
                #set DHCP gateway as metric 100
                if self.StandardDefaultGW != None:
                                self.SetGateway(self.StandardDefaultGW,100)
                                self.SetGateway(self.StandardDefaultGW,1)
                #set all gateways with metric top to down
                for a in self.Priorities:
                        Gateway = self.INI.getOptionStr("FAILOVER",a,"GATEWAY")
                        if Gateway != None:
                                # print "Gateway: ", Gateway
                                self.SetGateway(Gateway,Metric = StartMetric)
                                StartMetric += 1
                return
        
                        
        def SetGateway(self,Gateway,Metric = 1):
                DNS = ["172.26.144.8","8.8.8.8","8.8.4.4"]
                self.SetDNS(DNS)
                Metric = str(Metric)
                
                # self.log.printError("route add default gw " + Gateway + " metric " + Metric)
                if lib_Bash.Bash("sudo route add default gw " + Gateway + " metric " + Metric):

                        self.log.printError( "Failed to set Gateway")
                        return True
                else:
                        self.log.printOK("Gateway %s \tset with metric %s"%(Gateway,Metric))
                

        def DelAllGateways(self):
                with open(os.devnull, 'w') as DEVNULL:
                        i = 0
                        while i<10:
                        
                                if lib_Bash.Bash("ip route del 0/0"):
                                        self.log.printOK( "All Gateways removed")
                                        break
                                i += 1
                                
        def DelGateway(self,Metric = 1):
                Metric = str(Metric)
                with open(os.devnull, 'w') as DEVNULL:
                        i = 0
                        while i<10:
                                if lib_Bash.Bash("ip route del 0/0 metric " + Metric):
                                        self.log.printOK( "Gateways with metric %s removed"%Metric)
                                        break
                                i += 1
                                
        def SetDNS (self,DNS):

                try:
                        content = ""
                        content += lib_Log.Banner()                                
                        content += lib_Log.FileWarning()
                        
                        for IP in DNS:
                                content += "nameserver " + IP + "\n"
                        
                        DNSList = open("/etc/resolv.conf", 'w')
                        DNSList.write(content)
                        DNSList.close()
                                
                except:
                        self.log.printError ("something went wrong")

        def GetCounters(self):
                result = {}
                temp = lib_LocalInterface.ReadBandwith(datatypes = self.CounterDatatypes, interfaces = self.CounterInterfaces)
                #part RX
                if temp["tun1"]["rx_bytes"] == None:
                        result["rxBytes"] = None
                else:
                        if self.rxBytes == None:
                                result["rxBytes"] = temp["tun1"]["rx_bytes"]
                        else:
                                try:
                                        result["rxBytes"] = int(temp["tun1"]["rx_bytes"]) - int(self.rxBytes)
                                except:
                                        result["rxBytes"] = None
                self.rxBytes = temp["tun1"]["rx_bytes"]

                #part TX
                if temp["tun1"]["tx_bytes"] == None:
                        result["txBytes"] = None
                else:
                        if self.txBytes == None:
                                result["txBytes"] = temp["tun1"]["tx_bytes"]
                        else:
                                try:
                                        result["txBytes"] = int(temp["tun1"]["tx_bytes"]) - int(self.txBytes)
                                except:
                                        result["txBytes"] = None
                self.txBytes = temp["tun1"]["tx_bytes"]
                return result

        def GetFailoverPriorities(self):
                FailoverEnable = self.INI.getOptionBool("FAILOVERGENERAL","FAILOVERENABLE")
                if FailoverEnable == False:
                        self.log.printWarning("Failover mechanism disabeled")
                        return None
                elif FailoverEnable:                       
                        Failover = self.INI.getOption("FAILOVER")
                        if Failover is None:
                                self.Error = True
                        Priorities = []
                        for devNumber in Failover:
                                try:
                                        Priorities.append(int(devNumber))
                                except KeyboardInterrupt:
                                        self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                                        exit()
                                except:
                                        pass
                        #rank priorities
                        Priorities.sort()
                        # cleanup Priorities
                        Priorities = self.CleanupPriorities(Priorities)
                        return Priorities
        def CleanupPriorities(self,Priorities):
                if Priorities == None:
                        return None

                copyPriorities = copy.deepcopy(Priorities)
                for Failover in copyPriorities:
                        if "RULE" in self.INI.getOption("FAILOVER",Failover):
                                rule = self.INI.getOptionStr("FAILOVER",Failover, "RULE")
                                #Remove Forbidden Priorities
                                if "forbid" == rule:
                                        Priorities.remove(Failover)
                                        self.log.printWarning("Failover%s is forbidden and therefore ignored" % Failover)
                                #if force, move to top of list
                                elif "force" == rule:
                                        Priorities.remove(Failover)
                                        Priorities.insert(0, Failover)
                                        self.log.printWarning("Failover%s is in a forced state and therefore has now highest priority" % Failover)

                return Priorities

        def WriteToDatabase(self):
                result = {}
                result["Description"] = self.Description
                result["Gateway"] = self.Gateway
                result["Interface"] = self.interface
                result["Policy"] = self.Policy
                result["Priority"] = self.Priority
                result.update(self.GetCounters())
                paramArray = {}
                paramArray["FAILOVER"] = {}
                paramArray["FAILOVER"][0] = {}
                paramArray["FAILOVER"][0]["General"] = result
                paramArray["FAILOVER"][0]["_ExtractInfo"] = {}
                paramArray["FAILOVER"][0]["_ExtractInfo"]["ExtractTime"] = time.time()
                # self.sql.WriteArrayData(self.INI,paramArray,uniqueTable = "failover")
                self.couch_db.write_default_values(self.INI, paramArray, uniqueTable = "failover")
                self.TweenTime = time.time()
                return

        def ClearFailoverVariables(self):
                self.Description = None
                self.Gateway = None
                self.interface = None
                self.Policy = None
                self.Priority = None
                self.MailMessage = None
                return
        def ReplaceMainGateway(self,FailoverNumber = None,DHCP = False):
                if DHCP == True:
                        if self.StandardDefaultGW == None:
                                # print "woops no Default gateway set"
                                return
                        Gateway = self.StandardDefaultGW

                        self.interface = self.config_interface
                        self.Policy = None
                        self.Description = "DHCP"
                        self.Priority = None
                else:
                        Gateway = self.INI.getOptionStr("FAILOVER",FailoverNumber,"GATEWAY")
                        if Gateway == None:
                                self.ClearFailoverVariables()
                                return
                        
                        self.interface = self.INI.getOptionStr("FAILOVER",FailoverNumber,"INTERFACE")
                        self.Policy = self.INI.getOptionStr("FAILOVER",FailoverNumber,"POLICY")
                        self.Description = self.INI.getOptionStr("FAILOVER",FailoverNumber,"DESCRIPTION")
                        self.Priority = str(FailoverNumber)
                self.Gateway = Gateway
                self.DelGateway(Metric = 1)
                self.SetGateway(Gateway,Metric = 1)
                self.ChangedInterfaceTime = time.time()
                self.LastSuccessVPNPing = time.time()
                self.WriteToDatabase()
                return
        def SetMessageChangeInterface(self,FailoverNumber = None,DHCP = False):
                if DHCP:
                        Message = "Failover switched to '%s'. This is a Fallback procedure as this gateway was not defined. \n" % self.Description
                        self.log.printWarning(Message)

                        Message += "\nYour prefered profile '%s' has no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",min(self.Priorities),"DESCRIPTION"))
                        for backup in self.Priorities:
                                if backup != min(self.Priorities):
                                        Message += "Profile '%s' with priority %s, has also no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",backup,"DESCRIPTION"),backup) 
                else:
                        if FailoverNumber != min(self.Priorities):
                                if self.Description == None:
                                        Message = "Failover switched to '%s'. This profile has priority %s. \n"%(self.interface,FailoverNumber)
                                else:
                                        Message = "Failover switched to '%s'. This profile has priority %s. \n"%(self.Description,FailoverNumber)
                                self.log.printWarning(Message)
                                Message += "\nYour prefered profile '%s' has no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",min(self.Priorities),"DESCRIPTION"))
                                for backup in self.Priorities:
                                        if backup != min(self.Priorities) and backup < FailoverNumber:
                                                Message += "Profile '%s' with priority %s, has also no internet connection.\n" % (self.INI.getOptionStr("FAILOVER",backup,"DESCRIPTION"),backup) 
                                Message += "\nPlease be aware of the change as it may result in expencive connectivity bills.\n"

                        else:
                                if self.Description == None:
                                        Message = "System returned to preferred Network '%s' \n"%(self.interface)
                                else:
                                        Message = "System returned to preferred Network '%s' \n"%(self.Description)
                                self.log.printOK(Message)
                Message += "\n\nThis is an autogenerated Message, pls do not reply!\n"
                Message += "\n\nBest Regards, \nRHBOX-Team"
                Message += "\n\n--------------------------------------------------"
                Message += "\nMailTimestamp: " + str(time.strftime("%Y-%m-%d %H:%M:%S")) + " UTC"
                self.MailMessage = Message

                #only send mail if required. If mail has not been send and we are back to the original interface, no mail should be send
                if self.InternalMailSend == False:
                        self.InterfaceBeforeLastMail = self.Description
                        self.ExternalMailSend = True
                        self.InternalMailSend = True
                #internalMailSend must be true (no mail send yet)for elif AND Description from now and past is not the same
                elif self.InterfaceBeforeLastMail != self.Description:
                        #comented this line. if at the end, this mail is not sended, we want to keep the description of previous interface
                        # self.InterfaceBeforeLastMail = self.Description
                        self.ExternalMailSend = True
                        self.InternalMailSend = True
                #internalMailSend must be true, (no mail send yet) and we are back to our original interface. No mails should be send anymore
                else:
                        self.ExternalMailSend = False
                        self.InternalMailSend = False

                
                return
        def SendMailIfRequired(self):
                if self.Ping.DoPingTest:
                        if self.InternalMailSend:
                                if (self.InternalMailDelay + self.ChangedInterfaceTime) < time.time():
                                        self.SendMail(MailDestination = "Internal")
                                        #added line to prevent sending to many emails
                                        self.InterfaceBeforeLastMail = self.Description
                                        self.InternalMailSend = False
                        if self.ExternalMailSend:
                                if (self.ExternalMailDelay + self.ChangedInterfaceTime) < time.time():
                                        self.SendMail(MailDestination = "External")
                                        #added line to prevent sending to many emails
                                        self.InterfaceBeforeLastMail = self.Description
                                        self.ExternalMailSend = False
                return
        def SendMail(self,MailDestination = "Internal"):

                print "preparing mail"
                #create Mail Instance
                Mail = lib_Mail.Mail(self.INI,"FAILOVERGENERAL",MailDestination = MailDestination)
                Mail.Set_Subject("Failover Event - %s - Changed to: %s - IMO: %s" % (self.INI.getOptionStr("INFO","VESSELNAME"),self.Description,self.INI.getOptionStr("INFO","IMO")))
                #print Message
                Mail.Set_Message(self.MailMessage)
                #Mail.Set_Attachement("/rhbox/log/","VSATBOX.log")

                #Create Mail thread
                MailThread = threading.Thread(target = Mail.Send_Mail)
                #if thread is deamon, we can kill it with ctrl + c
                MailThread.daemon = True
                #Start All Threads
                MailThread.start()

                #can not delete message as it can be send to internal and external
                # self.MailMessage = None
                del Mail
                return

        def CheckVPN(self):
                now = time.time()
                if self.PingVPN.DoPingTest:
                        self.LastSuccessVPNPing = now
                        if ((self.BurnedInterface == self.interface) and (self.interface != None)):
                                self.log.printWarning("Interface %s is unburned due to successfull ping VPN interface" % (self.BurnedInterface))
                                self.BurnedInterface = None
                elif (self.BurnedInterface != self.interface):
        
                        if (  (self.LastSuccessVPNPing + self.InterfaceBurnTime) < now ):
                                #current inteface must be burned
                                self.BurnedInterface = self.interface
                                self.log.printWarning("Interface %s is burned for %s seconds as VPN could not be established in %s seconds" % (self.interface,self.InterfaceBurnRestoreTime,self.InterfaceBurnTime))
                                self.InterfaceBurningTime = now
                        
                        
                        if (self.InterfaceBurningTime + self.InterfaceBurnRestoreTime) < now:
                                #current inteface must be unburned
                                self.log.printWarning("Interface %s is unburned due to elapsed time" % (self.BurnedInterface))
                                self.BurnedInterface = None

                return