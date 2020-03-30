
import os
import sys
import Class_GIT
import lib_Log

class Update(object):
        def __init__(self,INI,GitVersions):
                self.Error = False
                self.log = lib_Log.Log(PrintToConsole=True)
                self.INI = INI
                self.GitVersions = GitVersions
                self.RebootDisable = False

        def Update_All (self):
                self.log.mainTitle ("\nSTART Update Program")
                self.log.increaseLevel()
                self.GIT = Class_GIT.GIT (self.INI)
                self.GIT.ConnectDBServerVersions()
                self.Python_Update()
                self.PHP_Update()
                self.GIT.CloseDBServerVersions()
                self.Reboot()

        def Python_Update(self):
                self.log.printBoldInfo("Update Python")
                Program = "PYTHON"
                self.RebootDisable = self.GIT.Update(Program)

        def PHP_Update(self):
                self.log.printBoldInfo("Update PHP")
                Program ="WEB"
                self.GIT.Update(Program)

        def Reboot(self):
                """check for reboot"""
                self.log.printBoldInfo("Reboot")
                self.log.increaseLevel()
                #get values out ini-file
                softwareUpdateReboot = self.INI.getOptionBool("SOFTWARE_UPDATE","REBOOT")
                if softwareUpdateReboot is None:
                        self.Error = True

                if self.Error == False:
                        if self.RebootDisable == True:
                                if softwareUpdateReboot == True:
                                        self.log.printOK("Rebooting System")
                                        # os.system("sudo shutdown -r now")
                                        os.system("sudo service uwsgi restart && sudo service nginx restart")
                                else:
                                        self.log.printWarning("Reboot disabled by COMPLEXCONFIG.INI")
                        else:
                                self.log.printInfo("Reboot disabled when Python not updated")
                else:
                        self.log.printError("%s skipped due to previous failure" % sys._getframe().f_code.co_name)


        def __del__(self):
                pass
