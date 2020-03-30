import smtplib
import socket
import time
# from email.MIMEMultipart import MIMEMultipart
# from email.MIMEText import MIMEText
# from email.MIMEBase import MIMEBase

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

from email import encoders
import sys
import os

import lib_Log
 
class Mail(object):
        def __init__ (self,INI,Section,MailDestination = "Internal"):                
                self.log = lib_Log.Log(PrintToConsole=True)
                self.log.subTitle ("START Mail Program")
                self.INI = INI
                
                self.SmtpPort = 587
                # self.Smtp = "webmail.imtechmarine.com"
                # self.fromaddr = "noreply.rhbox@radioholland.com"
                # self.Username = "inet\\im-nl-sm-noreplyrhbo"
                # self.Password = "RHM@rine03"

                self.Smtp = "smtp.gmail.com"
                self.fromaddr = "noreply.rhbox@gmail.com"
                self.Username = "noreply.rhbox@gmail.com"
                self.Password = "NoReply@RHbox"

                # # self.Smtp = "10.2.86.117"
                # self.Smtp = "webmail.imtechmarine.com"
                # self.Username =  'noreply.rhbox2'
                # self.Password = "Welcome01!"
                # self.fromaddr = "noreply.rhbox2@rhmarinegroup.com"

                
                
                MailEnable = self.INI.getOptionBool(Section,"MAILENABLE")
                if MailEnable == None or MailEnable == False:
                        self.log.printWarning("Sending mail in '%s' is not enabled"%Section )
                        return

                if MailDestination.lower() == "internal":
                        Mailnumbers = self.INI.getOption(Section,"MAIL")
                elif MailDestination.lower() == "external":
                        Mailnumbers = self.INI.getOption(Section,"MAILEXTERNAL")
                if Mailnumbers is None:
                        self.log.printWarning("No %s mailaddresses for '%s' are configured"%(MailDestination.lower(),Section) )
                        return
                self.toaddr = []
                for Mailnumber in Mailnumbers:
                        Mail = self.INI.getOptionStr(Section,"MAIL",Mailnumber)
                        if Mail != None:
                                self.toaddr.append(Mail)
                self.msg = MIMEMultipart()
                 
                self.msg['From'] = self.fromaddr
                self.msg['To'] = ", ".join(self.toaddr)
        def Set_Subject(self,Subject):
                self.msg['Subject'] = Subject
        def Set_Message(self,Message):
                self.body = Message
                self.msg.attach(MIMEText(self.body, 'plain'))
        def Set_Attachement (self,Path , File):
        
                self.attachment = open(Path + File, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload((self.attachment).read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= %s" % File)
                self.msg.attach(part)
        def Send_Mail(self):
                try:
                        self.log.printInfo("Sending Mail..." )
                        time.sleep(1)
                        server = smtplib.SMTP(self.Smtp, self.SmtpPort,timeout = 300)
                        server.starttls()
                        server.login(self.Username, self.Password)
                        text = self.msg.as_string()
                        server.sendmail(self.fromaddr, self.toaddr, text)
                        server.quit()
                        self.log.printOK("Mail Sucesfully send" )
                except Exception as e:
                        self.log.printError( str(e))
                        try:
                                server.quit()
                        except:
                                pass
        def __del__(self):
                pass