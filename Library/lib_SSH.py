from pexpect import pxssh
import paramiko
import socket
import time
import sys
import os
import lib_Log
import lib_ICMP

class SSH():
        def __init__(self):
                self.log = lib_Log.Log(PrintToConsole=True)
                self.Error = False
                self.SSH_open  =  False
                self.SSH = paramiko.SSHClient()
                self.Prompt = ">"
                self.log.increaseLevel()
                self.ActiveMultiSession = False
        def SetPrompt(self,Prompt = ">"):
                self.Prompt = Prompt

        def  OpenConnection(self,Username = "intellian",Password = "12345678", IP = "192.168.0.3",Port = 22):
                """
                Opens  a SSH  connection  if  not  already  open
                """

                if self.Error == False:
                        PING = lib_ICMP.Ping(IP)
                        if PING.DoPingTest():
                                self.log.printInfo("Successfully Reached %s"%IP)
                        else:
                                self.log.printWarning("Can Not Reach %s" % IP)
                                self.Error = True

                if self.Error == False:
                        self.log.printInfo("Connecting SSH")

                        try:
                                self.SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                self.SSH.connect(IP, username=Username, password=Password, port=int(Port),timeout=50)
                                self.SSH_open  =  True
                                self.log.printInfo("SSH Connected")
                        except:
                                self.log.printError("%s SSH Connection Failed, Please Check Credentials" % sys._getframe().f_code.co_name)
                                self.Error = True
                return self.Error

        def  CloseConnection(self,Force=False):
                """
                Close  SSH connection
                """
                if  self.SSH_open or Force:
                        self.SSH.close()
                        self.SSH_open  =  False
                        self.log.printInfo("SSH Connection Closed")

        def SendCommandWithReturn (self,Command="?", Timeout=20, Method = 0):
                """
                Sends SSH command with return
                """
                result = None
                
                if self.Error == False:
                        if Method == 0:
                                stdin,stdout,stderr = self.SSH.exec_command(Command + "\n",timeout=Timeout)
                                #stdin.flush()

                        elif Method ==1:
                                stdin,stdout,stderr = self.SSH.exec_command("",timeout=Timeout)
                                stdin.write(Command + "\n" )
                                #stdin.flush()

                        else: #Method 2

                                # Send the command (non-blocking)
                                stdin, stdout, stderr = self.SSH.exec_command(Command,timeout=Timeout)
                                # Wait for the command to terminate
                                while not stdout.channel.exit_status_ready():
                                        # Only print data if there is data to read in the channel
                                        if stdout.channel.recv_ready():
                                                result = stdout.read()


                        if Method == 0 or Method == 1:
                                try:
                                        while True:
                                                buffer = stdout.channel.recv(1)
                                                if buffer == self.Prompt:
                                                        break
                                        result = ""
                                        while True:
                                                buffer = stdout.channel.recv(1)
                                                result = result + buffer
                                                if buffer == self.Prompt:
                                                        break

                                except socket.timeout as error:
                                        self.log.printError("SSH Timeout")
                                        self.Error = True

                                except Exception as e:
                                        self.log.printError("SSH Failure")
                                        self.log.printError(e)
                                        self.Error = True

                        if result != None:
	                        #remove last line
	                        result = result[:result.rfind('\n')]

                        return result

        def CreateSession(self,Command = "?", Timeout = 20):
                # Send the command (non-blocking)
                self.sshin, self.sshout, self.ssherr = self.SSH.exec_command(Command,timeout=Timeout)
                self.ActiveMultiSession = True

        def SendCommandInSession(self,Command = "?", Timeout = 20):
                if self.ActiveMultiSession:
                        self.sshin.write(Command + "\n")
                        self.sshin.flush()
        def CloseSessionWithReturn (self,Command = "?", Timeout = 20):
                if self.ActiveMultiSession:
                        self.sshin.write(Command + "\n")
                        self.sshin.flush()
                        self.ActiveMultiSession = False
                        # Wait for the command to terminate
                        while not self.sshout.channel.exit_status_ready():
                                # Only print data if there is data to read in the channel
                                if self.sshout.channel.recv_ready():
                                        result = self.sshout.read()
                        return result


