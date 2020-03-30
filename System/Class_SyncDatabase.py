# import MySQLdb #sudo apt-get install python-mysqldb
import sys
import os
import time
import lib_Log
# import lib_SQLdb
import lib_ICMP
import warnings
import re

class SyncDatabase(object):
        def __init__(self,INI,Policy = None):
                """
                Init vars
                Initial check
                """

                #general vars
                self.log = lib_Log.Log(PrintToConsole=True)
                self.INI = INI
                self.Error = False
                self.ForceAll = False
                self.syncTables = {}
                self.Policy = Policy

                #get dbName
                self.imoNumber = self.INI.getOptionStr("INFO","IMO")
                # self.dbName = "rhbox_" + self.imoNumber
                self.dbName = "rhdev_" + self.imoNumber

                #get server credentials
                self.DB_Remote_Host = self.INI.getOptionStr("DB_RHBOX_SERVER","HOST")
                self.DB_Remote_User = self.INI.getOptionStr("DB_RHBOX_SERVER","USER")
                self.DB_Remote_Password = self.INI.getOptionStr("DB_RHBOX_SERVER","PASSWORD")
                self.DB_Remote = lib_SQLdb.Database()

                #get localhost credentials
                self.DB_Local_Host = self.INI.getOptionStr("DB_LOCAL","HOST")
                self.DB_Local_User = self.INI.getOptionStr("DB_LOCAL","USER")
                self.DB_Local_Password = self.INI.getOptionStr("DB_LOCAL","PASSWORD")
                self.DB_Local = lib_SQLdb.Database()

                #check vars
                if None in (self.imoNumber, self.DB_Remote_Host, self.DB_Remote_User, self.DB_Remote_Password, self.DB_Local_Host, self.DB_Local_Password):
                        self.Error = True
                        self.log.printError("User, Host or Password not defined for local or remote SQL-server")

        def GetPolicy(self,Databases):

                ListTableNames  = []
                syncTables = {}
                self.log.printOK("Policy is currently set to '%s'" % self.Policy)
                #get all tables from Database
                for lines in Databases:
                        if "TableName" in lines:
                                tableNameTemp = lines["TableName"].split("_")[0]  #only keep everything before first "_"
                                m = re.search(r'\d+$', tableNameTemp)
                                if m:
                                        suffix = int(m.group())
                                else:
                                        suffix = ""
                                #if suffx found, remove it from the tableName
                                if suffix is not None:
                                        ListTableNames.append(tableNameTemp.rstrip(str(suffix)))
                #Get all policy arguments
                CleanPolicy = {}
                if self.Policy == None:
                        self.log.printWarning("NO Policy was set, therefore AllowAll is executed")
                        CleanPolicy = {}
                        CleanPolicy["ALLOWALL"] = True

                else:
                        PolicyDict = self.INI.getOption(self.Policy)
                        if PolicyDict == None:
                                self.log.printWarning("Policy '%s' is empty or unknown" % self.Policy)
                                return syncTables

                        #cleanup the Policy's and retreive bools
                        for keys in PolicyDict:
                                key = self.INI.getOptionBool(self.Policy,keys)
                                if key != None:
                                        CleanPolicy[keys] = key

                #Set all tables with a default policy - AllowAll if available
                DefaultPolicy = False
                if "ALLOWALL" in CleanPolicy:
                        DefaultPolicy = CleanPolicy["ALLOWALL"]
                        CleanPolicy.pop("ALLOWALL",None)

                if "RHBOXSYSTEM" in CleanPolicy:
                        key = self.INI.getOptionBool(self.Policy,"RHBOXSYSTEM")
                        if key != None:
                                if not "COREVALUES" in CleanPolicy:
                                        CleanPolicy["COREVALUES"] = key
                                if not "NTWCONF" in CleanPolicy:
                                        CleanPolicy["NTWCONF"] = key
                                if not "FAILOVER" in CleanPolicy:
                                        CleanPolicy["FAILOVER"] = key
                                if not "PARAMETERS" in CleanPolicy:
                                        CleanPolicy["PARAMETERS"] = key
                        CleanPolicy.pop("RHBOXSYSTEM",None)



                for key in ListTableNames:
                        syncTables[key] = DefaultPolicy

                #Set all policies as defined
                for key in CleanPolicy:
                        if key in syncTables:
                                syncTables[key] = CleanPolicy[key]
                        else:
                                self.log.printWarning("Policy '%s' is not defined in tables" % key)

                # remove all values wich are not set True
                result = {}
                for key in syncTables:
                        if syncTables[key] == True:
                                result [key] = True
                return result

        def SyncDatabase(self):
                """
                Sync Database
                """

                self.log.mainTitle("SYNC DATABASES")
                self.log.increaseLevel()

                #init vars
                # sql_procedureUpdateTblMax = {}
                # sql_procedureUpdateTblMax[1] = None # "DELIMITER //"
                # sql_procedureUpdateTblMax[2] = "DROP PROCEDURE IF EXISTS updateTblMaxIDs " #//"
                # sql_procedureUpdateTblMax[3] = ("##Create the function \n"
                #                                 "#WHEN THERE IS AN ERROR IN THIS FUNCTION, FIRST CHECK IF ALL YOURE TABLES HAVE AN 'ID' FIELD \n"
                #                                 "CREATE PROCEDURE updateTblMaxIDs() \n"
                #                                 "  MODIFIES SQL DATA \n"
                #                                 "BEGIN \n"
                #                                 "  #Declare some vars \n"
                #                                 "  DECLARE maxIDqry, tableName VARCHAR(250); \n"
                #                                 "  DECLARE done INT DEFAULT 0; \n"
                #                                 "  DECLARE MAXID INT; \n"
                #                                 " \n"
                #                                 "  #Get a table like this: \n"
                #                                 "  # o--------------------------------------o--------o \n"
                #                                 "  # | SELECT MAX(ID) IN @MAXID FROM table1 | table1 | \n"
                #                                 "  # | SELECT MAX(ID) IN @MAXID FROM table2 | table2 | \n"
                #                                 "  # | SELECT MAX(ID) IN @MAXID FROM table3 | table3 | \n"
                #                                 "  # | ...                                  | ...    | \n"
                #                                 "  # o--------------------------------------o--------o \n"
                #                                 "  DECLARE table_cur CURSOR FOR \n"
                #                                 "        SELECT concat('SELECT MAX(`ID`) INTO @MAXID FROM `', TABLE_NAME , '` WHERE 1 ') , TABLE_NAME as `tableName` FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='" + self.dbName + "'; \n"
                #                                 " \n"
                #                                 "  #Create handler (?) \n"
                #                                 "  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done=1; \n"
                #                                 " \n"
                #                                 "  #Create temporary table \n"
                #                                 "  DROP TEMPORARY TABLE IF EXISTS outputTable; \n"
                #                                 "  CREATE TEMPORARY TABLE outputTable (`TableName` varchar(250) NOT NULL,`MaxID` int(20) NOT NULL); \n"
                #                                 " \n"
                #                                 "  #loop over results \n"
                #                                 "  OPEN table_cur; \n"
                #                                 " \n"
                #                                 "    table_loop:LOOP \n"
                #                                 "        #get data out of results \n"
                #                                 "        FETCH table_cur INTO maxIDqry, tableName; \n"
                #                                 " \n"
                #                                 "        #get maxID \n"
                #                                 "        SET @maxIDqry = maxIDqry; \n"
                #                                 "        PREPARE maxIDqry FROM @maxIDqry; \n"
                #                                 "        EXECUTE maxIDqry; \n"
                #                                 "        SET MAXID = @MAXID; \n"
                #                                 " \n"
                #                                 "        #check if done \n"
                #                                 "        IF done=1 THEN \n"
                #                                 "                LEAVE table_loop; \n"
                #                                 "        END IF; \n"
                #                                 " \n"                                                
                #                                 "        #insert if maxID > 0 \n"
                #                                 "        #IF MAXID>0 THEN \n"
                #                                 "                # Inserting results \n"
                #                                 "                INSERT INTO outputTable VALUES(tableName,MAXID); \n"
                #                                 "        #END IF; \n"
                #                                 " \n"
                #                                 "        END LOOP table_loop;  \n"
                #                                 "  CLOSE table_cur; \n"
                #                                 " \n"
                #                                 "  #Finally Show Results \n"
                #                                 "  SELECT * FROM outputTable; \n"
                #                                 " \n"
                #                                 "END " #// \n"
                #                                 )
                # sql_procedureUpdateTblMax[4] =  None #"DELIMITER ;"

                #open connection to local DB
                if self.Error == False:
                        self.log.printBoldInfo("Open connection to local database")
                        self.log.increaseLevel()
                        connectionFailed = self.DB_Local.OpenConnection(self.DB_Local_User, self.DB_Local_Password, self.DB_Local_Host, self.dbName)
                        if connectionFailed:
                                self.log.printError("Error in opening connection to local database")
                                self.Error = True
                        self.log.decreaseLevel()

                #get all tables and max ID's from local database
                if self.Error == False:
                        self.log.printBoldInfo("Get all tables and max ID's from local database")
                        self.log.increaseLevel()

                        #run query                                                                        
                        self.DB_Local_TablesAndMaxIDs = self.DB_Local.CallProc('getTblMaxIDs')                        

                        #check if error
                        if self.DB_Local.Error == True:
                                self.log.printError("Error during executing query")
                                self.Error = True

                        self.log.decreaseLevel()

                #Get Sync policies
                if self.Error == False:
                        self.log.printBoldInfo("Get Policies")
                        self.log.increaseLevel()
                        self.syncTables = self.GetPolicy(self.DB_Local_TablesAndMaxIDs)
                        if self.syncTables == {}:
                                self.log.printWarning("Policy forbids syncing")
                        self.log.decreaseLevel()

                #open connection to remote DB
                if self.Error == False and not self.syncTables == {}:
                        self.log.printBoldInfo("Open connection to remote database")
                        self.log.increaseLevel()
                        connectionFailed = self.DB_Remote.OpenConnection(self.DB_Remote_User, self.DB_Remote_Password, self.DB_Remote_Host, self.dbName)
                        if connectionFailed: #connection failed or database doesn't exist on en remote
                                #retry to connect without database
                                self.DB_Remote.Error = False
                                self.log.printBoldInfo("Not able to connect with database, try to connect to server without database")

                                #Connect without database
                                connectionFailed = self.DB_Remote.OpenConnection(self.DB_Remote_User, self.DB_Remote_Password, self.DB_Remote_Host, None)
                                if connectionFailed: #connection failed
                                        self.log.printError("Error in opening connection to remote database")
                                        self.Error = True
                                else: #connection succesfull - database doesn't exists
                                        self.log.printBoldInfo("Create database on remote server if not exists")

                                        #enable filters
                                        warnings.simplefilter('ignore')

                                        #Check If Database exist and create if not
                                        try:
                                                sql = ('CREATE DATABASE IF NOT EXISTS %s' % self.dbName)
                                                self.DB_Remote.Execute(sql)                                                
                                                self.log.printInfo("Succesfully Created Database %s" % self.dbName)                                        
                                                self.log.printInfo("Add procedures to database")
                                                try:
                                                        #switch to current db
                                                        self.DB_Remote.Execute("USE `" + self.dbName + "`")
                                                        self.DB_Remote.Commit()
                                                        #add procedures
                                                        sql_procedureUpdateTblMax = lib_SQLdb.getProceduresQuery(self.dbName)
                                                        for sqlID in sql_procedureUpdateTblMax:                                                                
                                                                sql = sql_procedureUpdateTblMax[sqlID]                                                                
                                                                self.DB_Remote.Execute(sql)
                                                                self.DB_Remote.Commit()
                                                        self.log.printInfo("Succesfully added procedures")
                                                except:
                                                        self.log.printError("Failed to add procedures")
                                                        self.Error = True                                                                        
                                        except:
                                                self.log.printError("Failed to Create Database %s" % self.dbName)
                                                self.Error = True                                                        

                        self.log.decreaseLevel()

                #get all tables and max ID's from remote database
                if self.Error == False and not self.syncTables == {}:
                        self.log.printBoldInfo("Get all tables and max ID's from remote database")
                        self.log.increaseLevel()

                        #run query                                                                        
                        self.DB_Remote_TablesAndMaxIDs = self.DB_Remote.CallProc('getTblMaxIDs')                        

                        #check if error
                        if self.DB_Remote.Error == True:
                                self.log.printError("Error during executing query")
                                self.Error = True

                        self.log.decreaseLevel()

                #rebuild fetched results
                if self.Error == False and not self.syncTables == {}:
                        #builds dict with following format
                        #  [tableName] : [
                        #                  [local] : <MaxID>
                        #                  [remote]: <MaxID>
                        #                ]

                        #init vars
                        self.tablesMaxIDs = {}
                        self.tablesToBeCreates = {}

                        #loop over results - local
                        for dataRow in self.DB_Local_TablesAndMaxIDs:
                                self.tablesMaxIDs[dataRow["TableName"]] = {}
                                self.tablesMaxIDs[dataRow["TableName"]]["local"] = dataRow["MaxID"]
                                self.tablesMaxIDs[dataRow["TableName"]]["remote"] = 0
                                self.tablesMaxIDs[dataRow["TableName"]]["existsOnRemote"] = False

                        #loop over results - remote
                        for dataRow in self.DB_Remote_TablesAndMaxIDs:
                                #if table name is in local, add it to dict
                                if dataRow["TableName"] in self.tablesMaxIDs:
                                        self.tablesMaxIDs[dataRow["TableName"]]["remote"] = dataRow["MaxID"]
                                        self.tablesMaxIDs[dataRow["TableName"]]["existsOnRemote"] = True

                #remove all tables where local ID is equal to remote ID
                if self.Error == False and not self.syncTables == {}:
                        #title
                        self.log.printBoldInfo("Filter out tables that not need to be synced")
                        self.log.increaseLevel()

                        skippingPolicy = {}
                        skippingSyncOK = {}

                        #build syncTablesTrue:
                        #same as self.syncTables but only with true values
                        syncTablesTrue = {}
                        for tableName in self.syncTables:
                                if self.syncTables[tableName]:
                                        syncTablesTrue[tableName] = True

                        #loop over tables
                        for tableName in sorted(self.tablesMaxIDs.keys(), reverse=False): #! Reverse important, first modules and options should be done, general as last !
                                #get trailing number and suffixes (e.g. VSAT1 => 1 or VSAT1_Modules => 1_Modules)
                                tableNameTemp = tableName.split("_")[0]  #only keep everything before first "_"
                                m = re.search(r'\d+$', tableNameTemp)
                                if m:
                                        suffix = int(m.group())
                                else:
                                        suffix = ""

                                #if suffx found, remove it from the tableName
                                if suffix is not None:
                                        tableNameTemp = tableNameTemp.rstrip(str(suffix))

                                if tableNameTemp not in syncTablesTrue:
                                        #self.log.printWarning("[Skipping sync]\t %s - Not syncing due to policy" % tableName)
                                        skippingPolicy[tableName] = None
                                        del self.tablesMaxIDs[tableName]
                                        continue

                                #check ids
                                localID = self.tablesMaxIDs[tableName]["local"]
                                remoteID = self.tablesMaxIDs[tableName]["remote"]

                                if (localID < remoteID):
                                        self.log.printError("Error: %s - Max. remoteID is higher than localID" % tableName)
                                        del self.tablesMaxIDs[tableName]
                                        continue
                                elif(localID == remoteID):
                                        #self.log.printInfo("[Skipping sync]\t %s - Allready in sync" % tableName)
                                        skippingSyncOK[tableName] = None
                                        del self.tablesMaxIDs[tableName]
                                        continue
                                elif(localID > remoteID):
                                        #self.log.printInfo("[Sync]\t\t %s - %s item(s) need to be synced" % (tableName, (localID - remoteID)))
                                        pass
                                else:
                                        pass

                        if len(skippingPolicy.keys()) > 0:
                                i = 0
                                tempStr = ""
                                for tableName in sorted(skippingPolicy.keys()):
                                        i += 1; tempStr += tableName
                                        if (i < len(skippingPolicy.keys())):
                                                tempStr += ", "
                                                if ((i % 5) == 0):
                                                        tempStr += "\n      "
                                self.log.printBoldInfo("Syncing skipped due to failover policy:")
                                self.log.printInfo("  %s" % tempStr)

                        if len(skippingSyncOK.keys()) > 0:
                                i = 0
                                tempStr = ""
                                for tableName in sorted(skippingSyncOK.keys()):
                                        i += 1; tempStr += tableName
                                        if (i < len(skippingSyncOK.keys())):
                                                tempStr += ", "
                                                if ((i % 5) == 0):
                                                        tempStr += "\n      "
                                self.log.printBoldInfo("Syncing skipped - Allready in sync:")
                                self.log.printInfo("  %s" % tempStr)

                        #back to default indent
                        self.log.decreaseLevel()

                #create tables on remote
                if self.Error == False and not self.syncTables == {}:
                        #title
                        self.log.printBoldInfo("Create tables on remote (if needed)")
                        self.log.increaseLevel()

                        #loop over tables
                        for tableName in sorted(self.tablesMaxIDs.keys(), reverse=False): #! Reverse important, first modules and options should be done, general as last !
                                existsOnRemote = self.tablesMaxIDs[tableName]["existsOnRemote"]
                                if existsOnRemote == False:
                                        self.log.printInfo("Creating table %s" % tableName)
                                        #create query
                                        sql = "SHOW CREATE TABLE `" + self.dbName + "`.`" + tableName + "`"

                                        #run query
                                        self.DB_Local.Execute(sql)
                                        result = self.DB_Local.Fetch()

                                        #check if error
                                        if self.DB_Local.Error == True:
                                                self.log.printError("Error during executing query")
                                                self.Error = True
                                        else:
                                                for dataRow in result:
                                                        if "Create Table" in dataRow:
                                                                #get table constructor
                                                                sqlCreateTable = dataRow["Create Table"]

                                                                #set auto_increment counter to 1
                                                                regex = r'AUTO_INCREMENT\s?=\s?\d*'
                                                                subst = "AUTO_INCREMENT = 1"
                                                                sqlCreateTable = re.sub(regex, subst, sqlCreateTable, 1, re.IGNORECASE)

                                                                #switch to current db and create table
                                                                self.DB_Remote.Execute("USE `" + self.dbName + "`")
                                                                #self.DB_Remote.Commit()
                                                                self.DB_Remote.Execute(sqlCreateTable)
                                                                self.DB_Remote.Commit()
                                                                if self.DB_Remote.Error == False:
                                                                        self.log.printOK("Table created")
                        #back to default indent
                        self.log.decreaseLevel()


                #do actual inserts
                if self.Error == False and not self.syncTables == {}:
                         #title
                        self.log.printBoldInfo("Add Data to tables")
                        self.log.increaseLevel()

                        #loop over tables
                        for tableName in sorted(self.tablesMaxIDs.keys(), reverse=False): #! Reverse important, first modules and options should be done, general as last !
                                self.log.printBoldInfo(tableName)
                                self.log.increaseLevel()

                                #check ids
                                localID = self.tablesMaxIDs[tableName]["local"]
                                remoteID = self.tablesMaxIDs[tableName]["remote"]
                                #double check
                                if (remoteID >= localID):
                                        self.log.printError("Error - max remote ID is higher than max local ID")
                                        continue #skipp current for-loop

                                maxNumberOfRowToSyncAtOnce = 5000
                                lastSelectedRow = 0 #don't change this
                                totalRowsSynced = 0

                                #Insert/update multiple rows at once
                                #But do it in blocks of "maxNumberOfRowToSyncAtOnce" lines
                                while True:
                                        lowerLimit = lastSelectedRow
                                        upperLimit = lastSelectedRow + maxNumberOfRowToSyncAtOnce - 1
                                        lastSelectedRow = upperLimit + 1

                                        query = "SELECT * FROM `" + self.dbName + "`.`" + tableName + "` WHERE `ID`> " + str(remoteID) + " ORDER BY `ID` ASC LIMIT " + str(lowerLimit) + ", " + str(maxNumberOfRowToSyncAtOnce) + ";"

                                        queryResult = self.DB_Local.Execute_AND_Fetchall(query)
                                        columns = ""
                                        updateColumns =""
                                        values = ""
                                        valuesTemp = ""
                                        columnsRunOnce = True
                                        i = 0
                                        # Loop over al rows from previouis query and build parts of insert query
                                        for row in queryResult:
                                                valuesTemp = ""
                                                for column in row:
                                                        #build variable which holds the column-names of the table
                                                        if columnsRunOnce:
                                                                columns = "`" + str(column) + "`, " + columns
                                                                updateColumns = "`" + str(column) + "`=VALUES(`" + str(column) + "`), " + updateColumns

                                                        #check type of variable and add quotes if necessary (e.g. for text)
                                                        if (row[column] is None):
                                                                valuesTemp = "NULL" + ", " + valuesTemp
                                                        elif (type(row[column]) == int):
                                                                valuesTemp = str(row[column]) + ", " + valuesTemp
                                                        elif(type(row[column]) == long):
                                                                valuesTemp = str(row[column]) + ", " + valuesTemp
                                                        elif(type(row[column]) == str):
                                                                valuesTemp = "'" + str(row[column]) + "', " + valuesTemp
                                                        else:
                                                                valuesTemp = "'" + str(row[column]) + "', " + valuesTemp

                                                columnsRunOnce = False #we only need the columns once for multiple rows
                                                valuesTemp = "(" + valuesTemp.strip(", ") + ")"
                                                values += str(valuesTemp) + ", "
                                                i += 1

                                        #tidy up the builded strings
                                        columns = "(" + columns.strip(", ") + ")"       #(`Clmn1`,`Clmn2`,`Clmn3`)
                                        updateColumns = updateColumns.strip(", ")       #`Clmn1`=VALUES(`Clmn1`),`Clmn2`=VALUES(`Clmn2`),`Clmn3`=VALUES(`Clmn3`)
                                        values = "" + values.strip(", ") + ""           #(`Val1`,`Val2`,`Val3`),(`Val1`,`Val2`,`Val3`),(`Val1`,`Val2`,`Val3`)

                                        #if rows need to be inserted, insert them
                                        if (i > 0):
                                                #INSERT INTO table (a,b,c) VALUES (1,2,3),(4,5,6),(7,8,9)
                                                query = "INSERT INTO `" + self.dbName + "`.`" + tableName + "` " + columns + " VALUES " + values + ";"
                                                self.log.printInfo("Inserting rows " + str(lowerLimit + 1) + " to " + str(lowerLimit + i))
                                                self.DB_Remote.Execute_AND_Commit(query)
                                                totalRowsSynced += i

                                        #if end of table has reached, stop while loop
                                        if (i < (maxNumberOfRowToSyncAtOnce -1)):
                                                break

                                self.log.printOK(str(totalRowsSynced) + " rows inserted")

                                #back to previous indent
                                self.log.decreaseLevel()

                        #back to default indent
                        self.log.decreaseLevel()

                #close connection to local DB
                #if self.Error == False and self.DB_Local.SQL_open == True:
                if self.DB_Local.SQL_open == True:
                        self.log.printBoldInfo("Close connection to local database")
                        self.log.increaseLevel()

                        self.DB_Local.CloseConnection()

                        self.log.decreaseLevel()

                #close connection to remote DB
                #if self.Error == False and self.DB_Remote.SQL_open == True:
                if self.DB_Remote.SQL_open == True:
                        self.log.printBoldInfo("Close connection to remote database")
                        self.log.increaseLevel()

                        self.DB_Remote.CloseConnection()

                        self.log.decreaseLevel()


