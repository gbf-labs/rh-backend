import lib_Log
import lib_Bash
import Class_SSH

class NetworkConfig(object):


        def __init__(self,INI):
                self.log = lib_Log.Log(PrintToConsole=True)
                self.Error = False
                self.INI = INI
        def CreateOpenVPNFile(self):
                OpenVPNString = ""
                OpenVPNString += lib_Log.Banner()                                
                OpenVPNString += lib_Log.FileWarning()
                OpenVPNString += "client \n"
                OpenVPNString += "dev tun \n"
                OpenVPNString += "proto tcp \n"
                OpenVPNString += "remote 185.95.73.13 11999 \n"
                OpenVPNString += "resolv-retry infinite \n"
                OpenVPNString += "nobind \n"
                OpenVPNString += "persist-key \n"
                OpenVPNString += "persist-tun \n"
                OpenVPNString += "ca ./ca.crt \n"
                OpenVPNString += "cert ./rhbox" + IMO + ".crt \n"
                OpenVPNString += "key ./" + IMO + ".key \n"
                OpenVPNString += "ns-cert-type server \n"
                OpenVPNString += "comp-lzo \n"
                OpenVPNString += "log-append log/openvpn.log \n"
                OpenVPNString += "verb 3 \n"
                OpenVPNString += "keepalive 20 60 \n"
                
                try:
                        OVPNFile = open("/etc/openvpn/rhbox_server.conf", 'w')
                        OVPNFile.write(OpenVPNString)
                        OVPNFile.close()
                except KeyboardInterrupt:
                        self.log.printError ("\nMain Program stopped by User (CTRL+C)")     
                        exit()
                except:
                        self.log.printError ("Error writing /etc/openvpn/rhbox_server.conf")

                if lib_Bash.Bash("service openvpn restart"):
                        self.log.printError("could not restart openvpn")
                        return
                return
               
        def ConnectRemoteServer (self):
                pass
         
        def DisconnectRemoteServer (self):
                pass