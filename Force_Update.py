import directories
import Class_Update
import os
import sys
import lib_Log
import time
import Class_Update
import logging
import sys
import os

import Class_ReadConfigINI
import Class_Initialisation

#setup log File
log = lib_Log.Log(PrintToConsole = True)
log.mainTitle ("\n\n                     ")
log.mainTitle ("FORCED Update Program")

#initialisation
INIT = Class_Initialisation.Initialisation()        
result = INIT.Default_Initialisation()        
GitVersions = result["GitVersions"]
INI = result["INI"]

#Update
Update = Class_Update.Update(INI,GitVersions)
Update.Update_All()
log.increaseLevel()
log.printOK ("FORCED Update Program Finished")
