# from parse import *
import os
import sys
import lib_Log
# import lib_SQLdb
import lib_ICMP
import lib_Bash
import lib_config

import git
import subprocess
import requests
import re

class GIT(object):

    def __init__(self, INI):
    
        """ini GIT object"""
        # self.Error = False
        # self.log = lib_Log.Log(PrintToConsole=True)
        # self.INI = INI
        # cwd = os.getcwd()
        # self.GITDir = {"PYTHON" : cwd, "WEB" : "/rhbox/www/web/"}

        self.INI = INI

        self.vessel_number = INI.getOption("INFO","IMO")

        config_data = lib_config.CONFIG_DATA()
        
        # COUCH DATABASE NAME
        self.couchdb_name = config_data.couchdb_name

        # COUCH CREDENTIALS
        self.couch_protocol = config_data.couch_protocol
        self.couch_user = config_data.couch_user
        self.couch_password = config_data.couch_password
        self.couch_host = config_data.couch_host
        self.couch_port = config_data.couch_port

        self.remote_couch_protocol = config_data.remote_couch_protocol
        self.remote_couch_user = config_data.remote_couch_user
        self.remote_couch_password = config_data.remote_couch_password
        self.remote_couch_host = config_data.remote_couch_host
        self.remote_couch_port = config_data.remote_couch_port
        self.remote_db_name = config_data.remote_db_name

        self.backend_dir = config_data.backend_dir
        self.api_dir = config_data.api_dir
        self.web_dir = config_data.web_dir

        self.web_branch = config_data.web_branch
        self.api_branch = config_data.api_branch
        self.backend_branch = config_data.backend_branch

        self.log = lib_Log.Log(PrintToConsole = True)

    def couch_db_url(self, design=None):

        couch_query = self.couch_protocol + '://'+ self.couch_user 
        couch_query += ':' + self.couch_password + '@' + self.couch_host 
        couch_query += ':' + self.couch_port
        couch_query += '/' + self.couchdb_name + '/'

        if design:
            couch_query += design

        return couch_query

    def fetch_branch(self, dir):
        print("FETCH BRANCH!")

        try:
            command = "cd " + dir + ";git fetch --all"

            self.run_commands(command)

        except:

            print("Can't Connect to Git Server!")
            return 0

        return 1

    def current_branch(self, dir):
        print("CURRENT BRANCH!")

        command = "cd " + dir + ";git branch | grep \* | cut -d ' ' -f2"

        return self.run_commands(command)


    def all_branch(self, dir):
        print("All Branch!")

        command = "cd " + dir + ";git branch -r"

        return self.run_commands(command)

    def restart_service(self):
        print("RESTART SERVICE")

        command = "sudo chmod -R 777 /home/rh/backendv1/ini"

        self.run_commands(command)

        command = "sudo chmod -R 777 /home/rh/backendv1/SYSTEM.INI"

        self.run_commands(command)

        command = "sudo service uwsgi restart"

        self.run_commands(command)

        command = "sudo service nginx restart"

        self.run_commands(command)

        return 1


    def run_commands(self, command):

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
        output, _ = process.communicate()

        return output.decode('ascii')


    def run(self, force=False):

        self.log.mainTitle ("UPDATE GIT REPO")

        command = "sudo touch /home/rh/backendv1/config/branch.cfg"

        self.run_commands(command)

        command = "sudo chmod -R 777 /home/rh/backendv1/config/branch.cfg"

        self.run_commands(command)

        vessel_id = self.get_vessel(self.vessel_number)[0]['id']

        values = self.get_complete_values(
            vessel_id,
            "FAILOVER",
            flag='one_doc'
        )
        
        if not values: return 0

        policy = str(values['value']['FAILOVER']['General']['Policy'])

        self.log.mainTitle ("POLICY: " + str(policy))
        
        if policy == 'POL_ALLOWALL' or force == True:
        # if policy == 'POL_VSAT':

            dirs = []
            
            dirs.append({
                "repo": "web",
                "dir": self.web_dir,
                "branch": self.web_branch,
            })

            dirs.append({
                "repo": "api",
                "dir": self.api_dir,
                "branch": self.api_branch,
            })

            dirs.append({
                "repo": "backend",
                "dir": self.backend_dir,
                "branch": self.backend_branch,
            })

            flag = False
            for d in dirs:

                if self.update_repo(d):

                    flag = True

            if flag:

                self.restart_service()


    def update_repo(self, datas):
        dir = datas["dir"]

        self.fetch_branch(dir)

        if self.web_branch and self.api_branch and self.backend_branch:

            # CHECK IF BRANCH CHANGE
            cv = self.current_branch(dir)
            cv = str(cv).rstrip()
            # UPDATE IF CHANGE
            if cv != datas["branch"]:
                flag = False

                branches = self.all_branch(dir)
                for brnch in branches.split("\n"):
                    if str(brnch):
                        if str(brnch.split("origin/")[1]) == datas["branch"]:
                            flag = True

                if flag:

                    print("*"*50," UPDATE ", "*"*50)

                    command = "cd " + dir + ";git checkout " + str(datas["branch"])

                    print("RUN: Checkout!")
                    self.run_commands(command)

                    command = "cd /home/rh/apiv1;python3 setup.py"

                    print("RUN: API Setup!")
                    self.run_commands(command)

                    command = "cd /home/rh/apiv1;sudo pip3 install -r requirements.txt"

                    print("RUN: Install Requirements!")
                    self.run_commands(command)

                    print("*"*50," UPDATE ", "*"*50)
                
                    return 1

            return 0

        else:

            current_version = 0
            cv = self.current_branch(dir)
            if re.findall("master", cv, re.IGNORECASE):

                current_version = 0

            else:

                try:

                    current_version = cv.split("released/")[1]
                    float(current_version)

                except:

                    current_version = 0

            new_version = 0
            flag = False

            branches = self.all_branch(dir)
            for value in branches.split("\n"):
                pattern = 'origin\/released\/'
                value = str(value)
                if re.findall(pattern, value, re.IGNORECASE):
                    new_version = value.split("origin/released/")[1]
                    if float(current_version) < float(new_version):
                        flag = True

            if flag:

                print("="*50," UPDATE ", "="*50)

                command = "cd " + dir + ";git checkout released/" + str(new_version)

                print("RUN: Checkout!")
                self.run_commands(command)

                command = "cd /home/rh/apiv1;python3 setup.py"

                print("RUN: API Setup!")
                self.run_commands(command)

                command = "cd /home/rh/apiv1;sudo pip3 install -r requirements.txt"

                print("RUN: Install Requirements!")
                self.run_commands(command)

                uwsgi_ini_dir = "/etc/uwsgi/apps-available/api.ini"
                uwsgi_ini = ['[uwsgi]', 'socket = /run/uwsgi/app/api/socket',
                            'chdir = /home/rh/apiv1', 'master = true',
                            'plugins = python35', 'file = app.py',
                            'uid = www-data', 'gid = www-data',
                            'callable = APP', 'enable-threads = true',
                            'single-interpreter = true', '']

                with open(uwsgi_ini_dir, "w") as filename:

                    for line in uwsgi_ini:

                        filename.write(line+"\n")

                print("="*50," UPDATE ", "="*50)
            
                return 1

            return 0

    def get_vessel(self, imo, query=None):

        couch_query = self.couch_db_url()

        if not query == None:
            couch_query = query
        
        couch_query += '_design/vessel/_view/get_vessels?'
        couch_query += 'key="'+ imo +'"'

        # EXECUTE COUCH QUERY
        res = requests.get(couch_query)
        json_data = res.json()
        json_data = json_data['rows']

        # CHECK IF VESSEL EXIST
        if json_data:
            if json_data[0]['id']:
                return json_data
            else: return 0
        else:
            return 0
          
    def get_complete_values(self, vessel_id, device, start=None, end=None, flag='one', remote=None):

        couch_query = self.couch_db_url()
        
        if remote:
            couch_query = remote
        
        couch_query += '/_design/value/_view/get_value?'

        if start and end:
            couch_query += 'startkey=["' + vessel_id + '", "' + device + '",' + end + ']&'
            couch_query += 'endkey=["' + vessel_id + '", "' + device + '",' + start + ']'

            if flag == 'all':
                couch_query += '&include_docs=true&descending=true'
            else:
                couch_query += '&include_docs=true&limit=1&descending=true'
        
        else:
            couch_query += 'startkey=["' + vessel_id + '", "' + device + '",9999999999]&'
            couch_query += 'endkey=["' + vessel_id + '", "' + device + '",0]'

            if flag == 'all':
                couch_query += '&include_docs=true&descending=true'
            else:
                couch_query += '&include_docs=true&limit=1&descending=true'
        res =         requests.get(couch_query)
        json_data =   res.json()
        rows =        json_data['rows']
        data =        []
        if rows:

            if flag == 'one':

                if rows:
                    data = rows[0]['doc']['value']
            
            if flag == 'one_doc':

                if rows:
                    data = rows[0]['doc']
            
            elif flag == 'all':
            
                data = []
                for row in rows:

                    data.append(row['doc'])

        return data

    # def get_current_version(self, dir):

    #     command = "cd " + dir + ";git describe --tags --always"
    #     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    #     output = process.communicate()

    #     return str(output[0].split("\n")[0])

    # def fetch_branch(self, dir):
        
    #     command = "cd " + dir + ";git fetch --all"

    #     self.run_commands(command)

    #     return 1

    # def update_repo(self, dir, repo):

    #     command = "cd " + dir + ";git pull " + repo
    #     self.run_commands(command)

    #     return 1

# ================================== OLD SCRIPT ================================== #
    def Update(self,Program):
        """Get desired version from server """
        self.log.printInfo("Get desired Gitversion")
        GitVersion = self.Exchange_Versions_With_Remote(Program)

        """Update GIT"""
        if self.Error == False:
        
            Force = Program + "_FORCE_LATEST"

            RebootDisable = True
            GitLocal = self.GITDir[Program]

            try:
                g = git.cmd.Git(GitLocal)
                OriginalGitVersion = g.describe("--tags")
                self.log.printInfo("Update %s GIT from version '%s' to version '%s'"% (Program,OriginalGitVersion,GitVersion))

                forceUpdate = self.INI.getOptionBool("SOFTWARE_UPDATE",Force.upper())
                if forceUpdate == None:
                    forceUpdate = False
                if (OriginalGitVersion != GitVersion or forceUpdate == True or GitVersion == "latest" or GitVersion == "development"):
                    g.reset('--hard')
                    try:
                        g.reset('--hard', "FETCH_HEAD")
                    except:
                        self.log.printWarning("reset --hard FETCH_HEAD for '%s' failed" % GitLocal)
                    #Checking URL
                    CurrentURL = g.remote ("-v")
                    CurrentURL = CurrentURL.splitlines()[0]
                    CurrentURL = CurrentURL.split()
                    CurrentURL = CurrentURL[1]
                    #get credentials from INI
                    Password = self.INI.getOption("GIT_SERVER", "PASSWORD")
                    Host = self.INI.getOption("GIT_SERVER", "HOST")
                    User = self.INI.getOption("GIT_SERVER", "USER")
                    URL = self.INI.getOption("GIT_SERVER", "URL")
                    if URL != None and Host != None and User != None and Password != None:
                        RemoteURL =  "ssh://" + User + "@" + Host + ":" + URL + Program.lower() + ".git"
                        #set correct git URL
                        if CurrentURL != RemoteURL:
                            g.remote("set-url", "origin", RemoteURL )
                            self.log.printWarning("changed URL from '%s' to '%s'" % (CurrentURL,RemoteURL))



                        if not lib_Bash.Bash ("sshpass -p %s git -C %s pull" % (Password,GitLocal)):

                            if self.INI.getOptionBool("SOFTWARE_UPDATE",Force.upper()) == False and GitVersion != "latest" and GitVersion != "development":
                                #Try to go to Specific Version as descibed by remote
                                try:
                                    g.reset('--hard', GitVersion)
                                    self.log.printOK ("succesfully set %s version '%s'" % (Program,GitVersion))
                                except:
                                    self.log.printWarning ("GIT version '%s' is not found" % GitVersion)
                                    #Try to return to previous version"
                                    try:
                                        g.reset('--hard', OriginalGitVersion)
                                        self.log.printWarning ("Successfully rolled %s back to version '%s'" % (Program,OriginalGitVersion))
                                    except:
                                        self.log.printWarning ("Original %s GIT version '%s' is not found" % (Program,OriginalGitVersion))
                                        g.reset('--hard', "FETCH_HEAD")
                                        self.log.printWarning ("%s Went to latest available version in GIT" % Program)
                            elif GitVersion == "development":
                                DevelopVersion = g.describe("--tags")
                                self.log.printInfo("%s Development version is selected by Server" % Program)
                                self.log.printOK ("%s Went to latest available version '%s' in GIT" % (Program,DevelopVersion))
                            else:
                                result = g.tag()
                                Number = []

                                temp = result.split('\n')
                                for line in temp:
                                    try:
                                        Version = parse("Version_{Mayor}.{Minor}.{Build}",line)
                                        Number.append(int(Version["Mayor"]))
                                    except:
                                        pass
                                Mayor = max(Number)

                                Number= []
                                for line in temp:
                                    try:
                                        Version = parse("Version_{Mayor}.{Minor}.{Build}",line)
                                        result = int(Version["Mayor"])
                                        if result == Mayor:
                                            Number.append(int(Version["Minor"]))
                                    except:
                                        pass
                                Minor = max(Number)

                                Number= []
                                for line in temp:
                                    try:
                                        Version = parse("Version_{Mayor}.{Minor}.{Build}",line)
                                        result1 = int(Version["Mayor"])
                                        result2 = int(Version["Minor"])
                                        if result1 == Mayor and result2 == Minor:
                                            Number.append(int(Version["Build"]))
                                    except:
                                        pass
                                Build = max(Number)
                                LatestTag = "Version_%s.%s.%s"%(Mayor,Minor,Build)
                                g.reset('--hard', LatestTag)

                                if self.INI.getOptionBool("SOFTWARE_UPDATE",Force.upper()) == True:
                                    self.log.printWarning ("%s Forced to latest enabled by ini-file" % Program)
                                else:
                                    self.log.printWarning ("%s Forced to latest enabled by ServerDatabase as desiredversion = '%s'" % (Program,GitVersion))

                                self.log.printOK ("%s Went to latest available version '%s' in GIT" % (Program,LatestTag))
                else:
                    RebootDisable = False
                    self.log.printOK ("%s GIT does not require any update --> reboot disabled" % Program)
            except:
                self.log.printError ("Can not establisch GIT connection to remote")
                RebootDisable = False
                self.Error = True
        else:
            self.log.printError("%s skipped due to previous failure" % sys._getframe().f_code.co_name)
            self.Error = True
        self.log.printInfo("Push current Gitversion to Server for %s" % Program)
        self.Exchange_Versions_With_Remote(Program)
        return RebootDisable



    def Get_Version(self,GitFolder):
        """get git version"""
        if self.Error == False:
            try:
                g = git.cmd.Git(GitFolder)
                OriginalGitVersion = g.describe("--tags")
                return OriginalGitVersion
            except:
                self.log.printError ("Can not communicate with Git %s" % GitFolder)

    def Exchange_Versions_With_Remote(self,Gitname):
        if self.Error == False:
            OriginalGitVersion = self.Get_Version(self.GITDir[Gitname])
            Gitname = Gitname.lower()
            try:
                #get values out of ini-files
                imo = self.INI.getOption("INFO","IMO")
                vesselName = self.INI.getOption("INFO","VESSELNAME")
                if None in [imo, vesselName]:
                    self.Error = True

                """get versions out of remote server"""
                if self.Error == False:
                    sqlString =("SELECT `Desired_Version`,`Current_Version` FROM " + Gitname +" WHERE `IMO` = %s ",(imo))
                    self.sql.ExecuteTulip(sqlString)
                    ReadValue = self.sql.Fetch()
                    if ReadValue ==():
                        sqlString =("SELECT `Desired_Version`,`Current_Version` FROM " + Gitname +" WHERE `IMO` = %s ",(0))
                        self.sql.ExecuteTulip(sqlString)
                        try:
                            ReadValue = self.sql.Fetch()
                            sqlString =("INSERT INTO " + Gitname +" (`IMO`,`Vessel_Name`,`Current_Version`,`Desired_Version`)VALUES (%s,%s,%s,%s)",(imo,vesselName,OriginalGitVersion,ReadValue[0]["Desired_Version"]))
                            self.sql.ExecuteTulip(sqlString)
                            self.sql.Commit()
                        except:
                            ReadValue = (("*READ_Error*",OriginalGitVersion),)

                    elif ReadValue[0]["Current_Version"] != OriginalGitVersion:
                        sqlString =("UPDATE " + Gitname +" SET `Current_Version` = %s WHERE `IMO` = %s",(OriginalGitVersion,imo))
                        self.sql.ExecuteTulip(sqlString)
                        self.sql.Commit()

                    Desired_Version = ReadValue[0]["Desired_Version"]
                    return str(Desired_Version)
                else:
                    self.log.printError("%s skipped due to previous failure" % sys._getframe().f_code.co_name)

            except:
                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                self.Error = True
            
        
    def ConnectDBServerVersions(self):
        if self.Error == False:
        
            try:

                self.log.printBoldInfo("Connecting to Server")
                self.log.increaseLevel()

                #get credentials
                DBHost     = self.INI.getOption("DB_RHBOX_SERVER","HOST")
                DBUser     = self.INI.getOption("DB_RHBOX_SERVER","USER")
                DBPassword = self.INI.getOption("DB_RHBOX_SERVER","PASSWORD")
                dbName = "rhbox_Versions"

                if None in [DBHost, DBUser, DBPassword] :
                    self.log.printError("Host (%s), User (%s) or Password (%s) not defined for remote database" % (DBHost, DBUser, DBPassword))
                    self.error = True

                #open connection to database and create table
                if self.Error == False:
                    try:
                        self.sql = lib_SQLdb.Database()
                        if self.sql.OpenConnection(Username = DBUser,Password = DBPassword, IP = DBHost,dbName=dbName):
                            self.Error = True
                    except:
                        self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                        self.Error = True
            except:
                self.log.printError("%s Module Error" % sys._getframe().f_code.co_name)
                self.Error = True

    def CloseDBServerVersions(self):
        self.sql.CloseConnection()
        
    def __del__(self):
        pass

    
