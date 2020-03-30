import telnetlib
import time

import sys
import os

import lib_Log
import lib_ICMP

class Telnet (object):
        def __init__(self):
                self.log = lib_Log.Log(PrintToConsole=True)
                self.Error = False
                self.Telnet_open  =  False
                self.TelenetTimeout = 120
                self.Prompt = ">"
                self.log.increaseLevel()

        def  OpenConnection(self,IP = "192.168.0.3",Port = 23):
                """
                Opens  a Telnet  connection  if  not  already  open
                """
                if self.Error == False:
                        PING = lib_ICMP.Ping(IP)
                        if PING.DoPingTest():
                                self.log.printInfo("Successfully Reached %s"%IP)
                        else:
                                self.log.printWarning("Can Not Reach %s" % IP)
                                self.Error = True
                        
                        
                if self.Error == False:
                        '''
                        tn.read_until("login: ")
                        tn.write(user + "\n")
                        if password:
                            tn.read_until("Password: ")
                            tn.write(password + "\n")

                        '''
                
                        try:
                                self.Telnet = telnetlib.Telnet(IP,Port,self.TelenetTimeout)
                                self.log.printInfo("Telnet Connecting") 
                                self.Telnet_open  =  True
                        except:
                                self.log.printError("%s TELNET Connection Failed, Please Check Credentials" % sys._getframe().f_code.co_name)
                                self.Error = True
                return self.Error

        def  CloseConnection(self):
                """
                Close  Telnet connection
                """
                if self.Error == False:
                        if  self.Telnet_open:
                                self.Telnet.close()
                                self.Telnet_open  =  False
                                self.log.printInfo("Telnet Connection Closed")

        def WaitForCursor (self, ExpectBegin="?", Timeout=10):
                if self.Error == False:
                        if not isinstance(ExpectBegin, list):
                                ExpectBegin = [ExpectBegin]
                        self.Telnet.expect(ExpectBegin, Timeout)
        def SendCommandWithReturn (self, ExpectBegin="?", Command="?", ExpectEnd="?", Timeout=10):
                """
                Sends Telnet command with return
                """
                if self.Error == False:
                        if not isinstance(ExpectEnd, list):
                                ExpectEnd = [ExpectEnd]
                        self.Telnet.write(Command+"\n")
                        self.Telnet.read_until("\n", Timeout)
                        result = self.Telnet.expect(ExpectEnd, Timeout)[2]
                        #remove ending character
                        result = result[:-1]
                        
                        print("  " * self.log.level  + ".")
                        
                        return result
        def SendCommandWithoutReturn (self,Command="?", Prompt="?", Timeout=10):
                """
                Sends Telnet command with return
                """
                if self.Error == False:
                        if not isinstance(Prompt, list):
                                Prompt = [Prompt]

                        self.Telnet.write(Command+"\n")
                        self.Telnet.expect(Prompt, Timeout)

        def ExpectQuestion (self,Answer="?", Question ="?", Timeout=20,End = "\n"):
                """
                Sends Telnet Answer on question
                """
                if self.Error == False:
                        self.Telnet.read_until(Question, Timeout)
                        self.Telnet.write(Answer + End)

                        
        def ReturnQuestion (self, EndChar ="?", Timeout=20):
                """
                Sends Telnet Answer on question
                """
                if self.Error == False:
                        Question = self.Telnet.read_until(EndChar, Timeout)
                        return Question

        def Write (self, Command ="?",End = "\n"):
                """
                Sends Telnet Answer on question
                """
                if self.Error == False:
                        self.Telnet.write(Command + End)                      
                        
                        
                        
        def SendCommandWithReturn2 (self, Command="?", Timeout=10):
                """
                Sends Telnet command with return
                """
                if self.Error == False:
                        self.Telnet.write(Command+"\n")
                        self.Telnet.read_until("\n", Timeout)
                        result = self.Telnet.read_until(self.Prompt, Timeout)
                        result = result[:result.rfind('\n')]
                        print("  " * self.log.level  + ".")
                        return result
        def WaitForPrompt (self, Timeout=10):
                if self.Error == False:
                        self.Telnet.read_until(self.Prompt, Timeout)
        def SetPrompt(self,Prompt):
                self.Prompt = Prompt
        def ResetBuffer(self):
                test = self.Telnet.read_eager()