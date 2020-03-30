import directories
import Class_ReadConfigINI
import Class_GlobalMemory

#devices
import Class_Modem
import Class_VSAT
import Class_GIT
import Class_Initialisation
# import Class_SyncDatabase
import Class_SyncCouchDatabase
import Class_Switch
import Class_Update
import Class_GPS
import Class_GSM
import Class_NetworkPerformance
import Class_CoreValues
import Class_NetworkConfig
import Class_SNMP
import Class_PowerSwitch
import Class_Failover
import Class_FBB
import Class_IOP
import Class_Debian
import Class_BWTS
import Class_Mediator
import Class_NMEA
import Class_VDR
import Class_Router
import Class_SATC
import Class_VHF
import Class_AlarmPanel

import threading
import time
import datetime
import re
import copy
import sys
import os
import os.path

import lib_Log
import lib_Telnet
# import lib_SQLdb
import lib_CouchDB
import lib_Mail

import lib_config


#create smart devices
typeFunctions = {}
#IOP
typeFunctions["IOP"]            = Class_IOP.IOP
#FBB
typeFunctions["FBB"]            = Class_FBB.FBB
#Modem
typeFunctions["MODEM"]          = Class_Modem.Modem
#VSAT
typeFunctions["VSAT"]           = Class_VSAT.VSAT
#Switch
typeFunctions["SWITCH"]         = Class_Switch.Switch
#GPS
typeFunctions["GPS"]            = Class_GPS.GPS
#GSM
typeFunctions["GSM"]            = Class_GSM.GSM
#Ping Test
typeFunctions["NTWPERF"]        = Class_NetworkPerformance.NetworkPerformance
#INISNMPM
typeFunctions["INISNMP"]        = Class_SNMP.SNMP
#POWERSWITCH
typeFunctions["POWERSWITCH"]    = Class_PowerSwitch.PowerSwitch
#BWTS
typeFunctions["BWTS"]       = Class_BWTS.BWTS
#MEDIATOR
typeFunctions["MEDIATOR"]       = Class_Mediator.Mediator
#NMEA
typeFunctions["NMEA"]           = Class_NMEA.NMEA
#VDR
typeFunctions["VDR"]            = Class_VDR.VDR
#Router
typeFunctions["ROUTER"]         = Class_Router.Router
#SATC
typeFunctions["SATC"]         = Class_SATC.SATC
#VHF
typeFunctions["VHF"]         = Class_VHF.VHF
#AlarmPanel
typeFunctions["ALARMPANEL"]         = Class_AlarmPanel.AlarmPanel

#Loop amount as argument for main
LoopArgument = None
#skipboot amount as argument for main
skipBoot = False
#Check For Arguments given by start command
RemoteCommand = {}

lengthArgument = len(sys.argv)
i = 1
uniqueDevice = None   
OldTime =  datetime.datetime.now().time()

helpText = """
o===================o
| RHBox - Help-file |
o===================o

Available arguments:

    -?,-h,--help
            Shows this help-file
    -dev [device]
        Used to give a specific command to a device - defines which device
        e.g. -dev SWITCH1
    -cmd
        Used to give a specific command to a device - defines which command to be used
        see also -dev and -opt
        e.g. -cmd -reboot
    -opt [option]
        Used to give a specific command to a device - defines an option
        see also -dev and -cmd
        e.g. -opt Outlet1           
    -wwwuserip [userip]
        IP used by the web-user, used for loggings
        Used in combination with -dev, -cmd and -opt
    -loop [numberOfLoops]
        If given, program will stop after given ammount of loops
    -only [deviceType]
        If given, program will only run for the given deviceType
        e.g. -only SWITCH
    -skipboot
        Don't do the boot-routine when running

Other usefull commands:

    touch ini/run
        While program is running but idle (waiting for next start of loop),
        This command will initiate a new loop    
"""
dirs = ['log', 'ini']
for d in dirs:
    if not os.path.exists(d):
        os.makedirs(d)

config_data = lib_config.CONFIG_DATA()

if config_data.monitoring.upper() != "TRUE":
    print("Please enabled the monitoring!")
    sys.exit(0)

#// TODO //
# Use 'import argparse' Here !
#
while i+1 <= lengthArgument:
    # Show Help
    if (((sys.argv[i]).lower() == "-h") or ( (sys.argv[i]).lower() == "-?") or ((sys.argv[i]).lower() == "--help")):
        i-=1
        print(helpText)
        raise SystemExit(0)
    if (sys.argv[i]).lower() == "-dev":
        RemoteCommand["Device"] = sys.argv[i+1].upper()
    if (sys.argv[i]).lower() == "-cmd":
        RemoteCommand["Command"] = sys.argv[i+1].lower()
    if (sys.argv[i]).lower() == "-opt":
        RemoteCommand["Option"] = sys.argv[i+1].lower()
    if (sys.argv[i]).lower() == "-wwwuserip":
        RemoteCommand["wwwUserIP"] = sys.argv[i+1].lower()
    #Loop amount as argument for main
    if (sys.argv[i]).lower() == "-loop":        
        temp = sys.argv[i+1].lower()
        if temp.isdigit():
            LoopArgument = int(temp)
    if (sys.argv[i]).lower() == "-only":
        temp = sys.argv[i+1].upper()
        uniqueDevice = temp

        copyTypeFunctions = copy.deepcopy(typeFunctions)
        for devicetype in copyTypeFunctions:
            if devicetype != temp:
                typeFunctions.pop(devicetype,None)

    #skip first boot parameter
    if (sys.argv[i]).lower() == "-skipboot":
        skipBoot = True
        i-=1

    i += 2

if RemoteCommand == {}:
    NormalRun = True
    log = lib_Log.Log(PrintToConsole = True, LOG_FILENAME = 'log/RHBOX.log')
    print(lib_Log.Banner(WriteToFile = False) + lib_Log.consoleColors.ENDC)
else:
    NormalRun = False
    log = lib_Log.Log(PrintToConsole = True, LOG_FILENAME = 'log/HumanActivities.log')

if not NormalRun:
    #Main program printouts will only be found in the log, not on screen. This gives the option to have more feedback in log
    log.PrintToConsole = False
    log.mainTitle ("........................")
    log.mainTitle ("remote command initiated")

    if "Device" in RemoteCommand and "Command" in RemoteCommand:
        if not "Option" in RemoteCommand:
            RemoteCommand["Option"] = None
        if not "wwwUserIP" in RemoteCommand:
            RemoteCommand["wwwUserIP"] = None


        log.printInfo ("COMMAND = %s" % RemoteCommand["Command"])
        log.printInfo ("DEVICE = %s" % RemoteCommand["Device"])
        log.printInfo ("OPTION = %s" % RemoteCommand["Option"])
        log.printInfo ("wwwUserIP = %s" % RemoteCommand["wwwUserIP"])
        log.mainTitle ("........................")

        Device = RemoteCommand["Device"]

        #get trailing number (e.g. 1 in VSAT1)
        m = re.search(r'\d+$', Device)
        devNumber = int(m.group()) if m else None

        #if devNumber found, remove it from the Device name
        if devNumber is None:
            devName = Device.upper()
        else:
            devName = Device.rstrip(str(devNumber)).upper()

        INI = Class_ReadConfigINI.INI()

        #check if setgateway is required
        if RemoteCommand["Command"] == "setgateway":
            Failover = Class_Failover.Failover(INI)
            Failover.ManualGateway(RemoteCommand = RemoteCommand)
            log.mainTitle ("remote command finished\n\n\n")
            raise SystemExit(0)

        FilterINI = {}
        FilterINI[devName] = {}
        FilterINI[devName][devNumber] = INI.INI[devName][devNumber]

        INI.INI = FilterINI
        #Run the remote command on the specific device
        
        if devName in typeFunctions:
            typeFunctions[devName](INI,Command=RemoteCommand)
                    
    else:
        log.printError ("No Device or No Command was given")    
    log.mainTitle ("remote command finished\n\n\n")

if NormalRun:

    try:
        #create Memory Object
        memory = Class_GlobalMemory.GlobalMemory()

        #Start Program
        log.mainTitle ("\n\n                                   ")
        log.mainTitle ("  START Initialisation after boot  ")

        #Initialisation
        Error = True
        while Error:
            INIT = Class_Initialisation.Initialisation()
            result = INIT.Default_Initialisation()
            # GitVersions = result["GitVersions"]
            INI = result["INI"]

            if INIT.Error == False:
                Error = False
                del INIT
            else:
                log.printError ("Retry Initialisation in 10 sec due to Failure")
                time.sleep (10)   

        PortfowardRefreshRequired = True
        if not skipBoot:
            #Check/Change Hostname
            Class_Debian.CheckHostname(INI)       
            
            #Update Network Interfaces and dependencies
            PortfowardRefreshRequired = True
            
            log.subTitle ("Set Network Interfaces at boot")
            NetworkConfig = Class_NetworkConfig.NetworkConfig(INI,memory)
            NetworkConfig.SetInterfaces()
            PortfowardRefreshRequired = NetworkConfig.SetFirewall(PortfowardRefreshRequired)
            del NetworkConfig
    
            #Create Failover Thread
            Failover = Class_Failover.Failover(INI)
            Failoverthread = threading.Thread(target = Failover.AutoGateway)
            #if thread is deamon, we cal kill it with ctrl + c
            Failoverthread.daemon = True
            #Start All Threads
            Failoverthread.start()
        
        #set all counters/Variables
        StartTime = time.time()
        TweenTime = StartTime
        TimeLastUpdate = StartTime
        CoreInfo = {}
        i = 0

        while True:
            time.sleep (1)
            if INI.Check_All_New():
                log.subTitle ("Updating INI and Dependencies")

                #Cleanup
                del INI
                # del GitVersions
                #New Initialisation
                Error = True
                while Error:
                    INIT = Class_Initialisation.Initialisation()
                    result = INIT.Default_Initialisation()

                    # GitVersions = result["GitVersions"]
                    INI = result["INI"]
                    Failover.INI = INI
                    Failover.Renew = True

                    if INIT.Error == False:
                        Error = False
                        del INIT
                    else:
                        log.printError ("Retry Initialisation in 10 sec due to Failure")
                        time.sleep (10)
                #Check/Change Hostname
                Class_Debian.CheckHostname(INI)   
                PortfowardRefreshRequired = True
                log.printOK("Updating INI and Dependencies Finished")
                #Wait next cycle
                log.mainTitle ("Wait next Cycle Program\n")

            #Check for Updates
            mainUpdateTime  = INI.getOptionInt("MAIN_PROGRAM","MAINUPDATETIME")
            mainLoopTime    = INI.getOptionInt("MAIN_PROGRAM","MAINLOOPTIME")
            if mainUpdateTime is None:
                mainUpdateTime = 3600 * 24
                log.printWarning("Main update time time not defined in ini-file, set to %s seconds" % mainUpdateTime)

            if mainLoopTime is None:
                mainLoopTime = 60 * 10
                log.printWarning("Main loop time time not defined in ini-file, set to %s seconds" % mainLoopTime)

            # if Error == False:
            #     if ((time.time() - TimeLastUpdate) >= mainUpdateTime):
            #         Update = Class_Update.Update(INI,GitVersions)
            #         Update.Update_All()
            #         TimeLastUpdate = time.time()

            #if Loopt Agrument is assigned, exit when amout is reached
            if LoopArgument != None:
                if i >= LoopArgument:
                    log.printWarning("Program aborted as Loopammount '%s' has been reached" % LoopArgument)
                    break

            #check if file ini/run exists
            forcedRun = False
            if os.path.isfile('ini/run') == True:
                log.printWarning('Forced run by ini/run')
                #if file exists, remove it now
                os.remove('ini/run')
                #only set forcedRun if file is successfuly removed
                forcedRun = (os.path.isfile('ini/run') == False)

            #Start Cycle
            if Error == False:
                if (time.time() - TweenTime) >= mainLoopTime or i == 0 or forcedRun:
                    TweenTime = time.time()
                    i = i + 1
                    log.mainTitle ("\nSTART Cycle Program, Cycle %s" % i)
                    
                    #Threadingsettings
                    thread = INI.getOptionBool("MASTERSETTINGS","THREADINGENABLE")
                    if thread == True:
                        log.printWarning("Threading Enabled")
                        #Creating Threads
                        thread = {}
                        for device in typeFunctions:
                            thread[typeFunctions[device]] =   threading.Thread(target = typeFunctions[device], args=[INI], kwargs={"memory":memory})
                        #Starting Threads
                        for index in thread:
                            thread[index].start()
                        #Wait untill all Thread finished
                        for index in thread:
                            thread[index].join()
                    else:
                        log.printWarning("Threading Disabled")                                                
                        for device in typeFunctions:
                            typeFunctions[device](INI,memory = memory)  

                    #Update Network Interfaces and dependencies
                    log.subTitle ("Update Network Interfaces and Dependencies")
                    NetworkConfig = Class_NetworkConfig.NetworkConfig(INI,memory)
                    NetworkConfig.GetInterfaces()
                    PortfowardRefreshRequired = NetworkConfig.SetFirewall(PortfowardRefreshRequired)
                    del NetworkConfig

                    #Get CoreValues
                    CoreInfo["MainLoopTime"] = "{:.3f}".format(time.time() - TweenTime)
                    CoreInfo["Uptime"] = "{:.3f}".format(time.time() - StartTime)
                    CoreInfo["CycleCount"] = i
                    
                    Class_CoreValues.CoreValues(INI,memory,CoreInfo)

                    #create SQL instance
                    # sql = lib_SQLdb.Database() 
                    couch_db = lib_CouchDB.COUCH_DATABASE()

                    couch_db.write_default_values(INI, memory.DeviceArray, uniqueTable = uniqueDevice)
                    del memory
                    del couch_db

                    # SYNC DATABASE
                    # sync = Class_SyncDatabase.SyncDatabase(INI,Policy = Failover.Policy)
                    sync = Class_SyncCouchDatabase.SyncCouchDatabase(INI)
                    sync.SyncDatabase()
                    #Add CoreValue for next Run and clear all previous vallues
                    CoreInfo = {}
                    CoreInfo["TotalPrevLoopTime"] = "{:.3f}".format(time.time() - TweenTime)

                    #create Memory Object
                    memory = Class_GlobalMemory.GlobalMemory()
                    git_update = Class_GIT.GIT(INI)
                    git_update.run()

                    #Wait next cycle
                    Looptime = "{:.3f}".format(time.time() - TweenTime)
                    
                    log.mainTitle ("Wait next Cycle Program. Looptime was %s sec\n" % Looptime)
                else:
                    sys.stdout.write("\033[F") #back to previous line
                    sys.stdout.write("\033[K") #clear line
                    print("\rTime till next run: %s seconds" % (int(round(mainLoopTime - (time.time() - TweenTime)))))

    except KeyboardInterrupt:
        log.printError ("\nMain Program stopped by User (CTRL+C)")
    except Exception as e:

        INIT = Class_Initialisation.Initialisation()
        result = INIT.Default_Initialisation()

        INI = result["INI"]

        git_update = Class_GIT.GIT(INI)
        git_update.run(force=True)

        log.printError ("Mayor Error in Main Program, Reboot system in 5 minutes")
        print(e)
        time.sleep (300)
        os.system("sudo service uwsgi restart && sudo service nginx restart")
        # os.system("sudo shutdown -r now")
        
