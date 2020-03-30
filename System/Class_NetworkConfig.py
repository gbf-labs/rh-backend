import netifaces
import sys
import os
import time
import lib_Log
# import lib_SQLdb
import lib_Bash
import lib_config


class NetworkConfig(object):

    def __init__(self,INI,memory):
        self.memory = memory
        self.log = lib_Log.Log(PrintToConsole=True)
        self.Error = False
        self.INI = INI
        self.config_data = lib_config.CONFIG_DATA()
        return
             
    def SetInterfaces(self):
        SetVlanEnable = self.INI.getOptionBool("NETWORKGENERAL","SETVLANENABLE")
        
        if SetVlanEnable == None:
        
            self.log.printWarning("SetVlan enable option not found")
            self.log.printWarning("SetVlan mechanism disabeled")
        
        elif SetVlanEnable:
            self.log.printBoldInfo("SetVlan Mechanism Started")
            self.log.increaseLevel()
            
            VLANS = self.INI.getOption("VLAN")
            if VLANS is None:
                
                self.Error = True
                    
            else:

                InterfaceString = ""
                InterfaceString += lib_Log.Banner()                                
                InterfaceString += lib_Log.FileWarning()
                InterfaceString += "# interfaces(5) file used by ifup(8) and ifdown(8) \n"
                InterfaceString += " \n"
                InterfaceString += "# Please note that this file is written to be used with dhcpcd \n"
                InterfaceString += "# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf' \n"
                InterfaceString += " \n"
                InterfaceString += "# Include files from /etc/network/interfaces.d: \n"
                InterfaceString += "source-directory /etc/network/interfaces.d \n"
                InterfaceString += "# The loopback network interface \n"
                InterfaceString += "auto lo \n"
                InterfaceString += "iface lo inet loopback \n"
                InterfaceString += "\n"
                InterfaceString += "# This is a list of hotpluggable network interfaces. \n"
                InterfaceString += "# They will be activated automatically by the hotplug subsystem. \n"
                
                InterfaceString += "auto {0} \n".format(self.config_data.interface)
                InterfaceString += "iface {0} inet dhcp \n".format(self.config_data.interface)
                InterfaceString += "\tmetric 5 \n"
                InterfaceString += "\n"

                InterfaceString += "#Backup Network \n"
                InterfaceString += "auto {}:1 \n".format(self.config_data.interface)
                InterfaceString += "iface {}:1 inet static \n".format(self.config_data.interface)
                InterfaceString += "name Backup-Connection {}:1 \n".format(self.config_data.interface)

                InterfaceString += "\taddress 192.168.254.1 \n"
                InterfaceString += "\tnetmask 255.255.255.0 \n"
                InterfaceString += "\tbroadcast 192.168.254.255 \n"
                InterfaceString += "\tnetwork 192.168.254.0 \n"
                InterfaceString += "\n"
                for devNumber in VLANS:
                    try:
                        IP = self.INI.getOptionStr("VLAN",devNumber,"IP")
                        Netmask = self.INI.getOptionStr("VLAN",devNumber,"NETMASK")
                        if IP != None and Netmask != None:
                            InterfaceString += "#Define vlan%s \n" % devNumber
                            InterfaceString += "auto vlan%s \n" % devNumber
                            InterfaceString += "iface vlan%s inet static \n" % devNumber
                            InterfaceString += "\taddress %s \n" %IP
                            InterfaceString += "\tnetmask %s \n" % Netmask
                            InterfaceString += "\tvlan-raw-device {} \n\n".format(self.config_data.interface)  
                                
                    except KeyboardInterrupt:
                        self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                        exit()
                    except:
                        pass

                flag = False
                
                try:
                    with open("/etc/network/interfaces", 'r') as file:
                        current_interface = file.read()
                    if current_interface != InterfaceString:

                        flag = True
                        Interfaces = open("/etc/network/interfaces", 'w')
                        Interfaces.write(InterfaceString)
                        Interfaces.close()
                        self.log.printOK("Successfully written '/etc/network/interfaces' file")

                    else:
                        self.log.printOK("Nothing to change '/etc/network/interfaces' file")
                        
                except KeyboardInterrupt:
                    self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                    exit()
                except:
                    self.log.printError ("Error writing /etc/network/interfaces")

                self.RestartInterfaces()

                if flag:
                    
                    self.log.printWarning("Warning system will reboot in 20 seconds")
                    time.sleep(20)
                    os.system("sudo shutdown -r now")

                self.RemoveVlans()
                
                self.RestartInterfaces()
            
            self.log.decreaseLevel()
    
    def RemoveVlans(self):
        if self.Error == False:
            try:
                self.Interfaces = {}
                interface =  netifaces.interfaces()
                for vlan in interface:
                    if vlan [0:4] == "vlan":
                        self.log.printOK( "%s removed"%vlan)
                    
                        if lib_Bash.Bash("sudo vconfig rem {0}".format(vlan)):
                            self.log.printError( "Failed removing %s" %vlan)
                            return True
                        else:
                            self.log.printOK( "%s removed"%vlan)
                            
            except Exception as e:
                self.log.printError("GetVlans Failure")
                self.log.printError(e)
                self.Error = True       
    
    def GetInterfaces(self):
        if self.Error == False:
            self.log.printBoldInfo("Update Network Table")
            try:
                self.Interfaces = {}
                self.Interfaces["NTWCONF"] = {}
                self.Interfaces["NTWCONF"][0] = {}
                interface =  netifaces.interfaces()
                for i in interface:
                    result = netifaces.ifaddresses(i)
                    if i != "lo":
                        if netifaces.AF_INET in result:
                            if 'addr' in result[netifaces.AF_INET][0]:
                                self.Interfaces["NTWCONF"][0][i] = {}
                                self.Interfaces["NTWCONF"][0][i]["IP"] = result[netifaces.AF_INET][0]['addr']
                                self.Interfaces["NTWCONF"][0][i]["Netmask"] = result[netifaces.AF_INET][0]['netmask']
                                if i == self.config_data.interface:
                                    try:
                                        self.Interfaces["NTWCONF"][0][i]["MAC"] = netifaces.ifaddresses(self.config_data.interface)[17][0]['addr']
                                    except:
                                        self.log.printError("MAC for {} not found".format(self.config_data.interface))
                
                self.Interfaces["NTWCONF"][0]["_ExtractInfo"] = {}
                self.Interfaces["NTWCONF"][0]["_ExtractInfo"]["ExtractTime"] = time.time()
                self.memory.WriteMemory(self.Interfaces)
                #create SQL instance
                # sql = lib_SQLdb.Database()
                # sql.Create_General_Option_Module(self.INI,self.Interfaces,"NTWCONF1","Interface")
                
            except Exception as e:
                self.log.printError("GetInterface Failure")
                self.log.printError(e)
                self.Error = True

    def SetFirewall (self,UpdateRequired):
        if UpdateRequired != True:
            return False

        self.log.printInfo("Rebuidling Firewall required due to change INI files or First Boot")        
        if self.FlushFirewall():
            return True

        PortforwardUpdateRequired = self.SetPortforwarding()
        RoutesUpdateRequired = self.SetRoutes()

        if PortforwardUpdateRequired == False and RoutesUpdateRequired == False:
            return False
        return True

    def SetRoutes(self):
        self.log.printBoldInfo("Routing")
        self.log.increaseLevel()
        
        RoutesEnable = self.INI.getOptionBool("ROUTESGENERAL","ROUTESENABLE")
        if RoutesEnable == None or RoutesEnable == False:
            self.log.printWarning("Routes option 'RoutesEnable' is not set")
            return True
            
        Routes = self.INI.getOption("ROUTE")
        if Routes is None:
            self.Error = True
            return True
                
        else:
            #set route Rules
            for devNumber in Routes:
                Network = self.INI.getOptionStr("ROUTE",devNumber,"NETWORK")
                Netmask = self.INI.getOptionStr("ROUTE",devNumber,"NETMASK")
                Gateway = self.INI.getOptionStr("ROUTE",devNumber,"GATEWAY")
                Interface = self.INI.getOptionStr("ROUTE",devNumber,"INTERFACE")
                if Network != None and Netmask!= None and Interface!= None:
                    self.AddRoute(Network,Netmask,Interface,Gateway = Gateway)                                 

            return False

    def SetPortforwarding (self):
    
        self.log.printBoldInfo("Portforwarding")
        self.log.increaseLevel()
        
        PortForwardingEnable = self.INI.getOptionBool("PORTFORWARDINGGENERAL","PORTFORWARDINGENABLE")
        if PortForwardingEnable == None or PortForwardingEnable == False:
            self.log.printWarning("Portforwarding option 'PortForwardingEnable' is not set")
            return True

        PortForwarding = self.INI.getOption("PORTFORWARDING")
        if PortForwarding is None:
            self.Error = True
            return True
                
        else:
            #Enable Portforwarding
            if lib_Bash.Bash("sysctl -w net.ipv4.ip_forward=1"):
                self.log.printError("Failed to enable Portforwaring")
                return True
            #set Portforwarding Rules
            for devNumber in PortForwarding:
                Description = self.INI.getOptionStr("PORTFORWARDING",devNumber,"DESCRIPTION")
                SourcePort = self.INI.getOptionInt("PORTFORWARDING",devNumber,"SOURCEPORT")
                DestinationPort = self.INI.getOptionInt("PORTFORWARDING",devNumber,"DESTINATIONPORT")
                DestinationIP = self.INI.getOptionStr("PORTFORWARDING",devNumber,"DESTINATIONIP")
                if Description!= None and SourcePort!= None and DestinationPort!= None and DestinationIP!= None:
                    self.PortForwarding(SourcePort,DestinationIP,DestinationPort,Description)

            return False
                
    def FlushFirewall (self):
        if lib_Bash.Bash(["iptables -F",
        "iptables -X",
        "iptables -t nat -F",
        "iptables -t nat -X",
        "iptables -t mangle -F",
        "iptables -t mangle -X",
        "iptables -P INPUT ACCEPT",
        "iptables -P FORWARD ACCEPT",
        "iptables -P OUTPUT ACCEPT"]):
        
            self.log.printError("/rhbox/bash/FlushFirewall.sh Failed")
        
            return True
        
        else:
        
            self.log.printOK("Successfully Flushed Firewall")

                
    def PortForwarding(self,VPNPort,DestinationIP,DestinationPort,Description):
        Interface = "tun1"                                
        String1 = "iptables -t nat -A PREROUTING -i " + Interface + " -p tcp --dport " + str(VPNPort) + " -j DNAT --to " + DestinationIP + ":" + str(DestinationPort)
        String2 = "iptables -t nat -A POSTROUTING -p tcp -d " + DestinationIP + " --dport " + str(DestinationPort) + " -j MASQUERADE"
        if lib_Bash.Bash([String1,String2]):
            self.log.printError("Set PortForward tun1:%s \t --> \t %s:%s \t Failed for %s"% (VPNPort,DestinationIP,DestinationPort,Description))
            return True
        else:
            self.log.printOK("Set PortForward tun1:%s \t --> \t %s:%s \t successfully set for %s"% (VPNPort,DestinationIP,DestinationPort,Description))
                                
    def RestartInterfaces(self):
        self.log.printInfo ("Restarting interfaces")
        if lib_Bash.Bash("sudo /etc/init.d/networking restart"):
            self.log.printError( "Failed Restarting Network Interfaces")
            return True
        else:
            self.log.printOK( "Network Interfaces Restarted")

    def AddRoute(self,Destination,Mask,Interface,Gateway = None):
        try:
            self.log.increaseLevel()
            if Gateway == None:
                Gateway = ""
                GatewayText = ""
            else:
                GatewayText = "with gateway %s" % Gateway
                Gateway = " gw " + Gateway

            String1 = "route del -net " + Destination + " netmask " + Mask + Gateway
            if lib_Bash.Bash([String1]):
                pass
            else:
                self.log.printOK("removed existing duplicate route")

            String2 = "route add -net " + Destination + " netmask " + Mask + Gateway + " dev " + Interface
            if lib_Bash.Bash([String2]):
                self.log.printError("add route Destination : %s Mask : %s on Interface : %s %s Failed"% (Destination,Mask,Interface,GatewayText))
                self.log.decreaseLevel()
                return True
            else:
                self.log.printOK("add route Destination : %s Mask : %s on Interface : %s %s Successfull"% (Destination,Mask,Interface,GatewayText))
                self.log.decreaseLevel()
        except Exception as e:

            self.log.printError("error in adding route")
            self.log.printError("e")

