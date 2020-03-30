import os
import sys
import json
import copy
import time
import pprint
import lib_Log
import couchdb, requests
import lib_config
import Class_GlobalMemory
from jsonmerge import merge
import subprocess


class COUCH_DATABASE():

    def __init__(self):
        
        # INIT CONFIG
        config_data = lib_config.CONFIG_DATA()

        # COUCH DATABASE NAME
        self.couchdb_name = config_data.couchdb_name

        # COUCH CREDENTIALS
        self.couch_protocol = config_data.couch_protocol
        self.couch_user = config_data.couch_user
        self.couch_password = config_data.couch_password
        self.couch_host = config_data.couch_host
        self.couch_port = config_data.couch_port

        url = "{}://{}:{}@{}:{}/".format(self.couch_protocol, 
                                        self.couch_user,
                                        self.couch_password,
                                        self.couch_host,
                                        self.couch_port)

        # CREATE DATABASE
        create_database = self.create_database()

        self.vessel_number = ""
        self.vessel_id = ""

        self.backend_dir = config_data.backend_dir
        self.api_dir = config_data.api_dir
        self.web_dir = config_data.web_dir

        self.Error = False
        self.log = lib_Log.Log(PrintToConsole = True)
        self.log.increaseLevel()

    def create_database(self):

        url = self.couch_db_url()

        headers = {"Content-Type" : "application/json"}

        r = requests.put(url, headers=headers)

        json_data =   r.json()

        return json_data 

    def couch_db_url(self, design=None):

        couch_query = self.couch_protocol + '://'+ self.couch_user 
        couch_query += ':' + self.couch_password + '@' + self.couch_host 
        couch_query += ':' + self.couch_port
        couch_query += '/' + self.couchdb_name + '/'

        if design:
            couch_query += design

        return couch_query

    def couch_query_one(self, couch_query):

        res = requests.get(couch_query)
        json_data = res.json()
        if json_data['rows']:
            return json_data['rows'][0]
        else: 
            return {}

    def couch_query_all(self, couch_query):

        res = requests.get(couch_query)
        json_data = res.json()
        if json_data['rows']:
            return json_data['rows']
        else: 
            return []

    def check_design(self, design_id, url=None):
        if url == None:
            couch_query = self.couch_db_url()
        else:
            couch_query = url

        couch_query += design_id
        res = requests.get(couch_query)
        json_data = res.json()

        return json_data


    def insert_data(self, data, design=None):

        url = self.couch_db_url(design)

        headers = {"Content-Type" : "application/json"}

        r = requests.post(url, data=json.dumps(data),headers=headers)

        json_data =   r.json()

        return json_data

    def couch_create_databases(self, imo, db=None, url=None):

        self.vessel_number = imo
        # VESSEL TABLE
        design_id = "_design/vessel"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": { 
                       "get_vessels": 
                            {"map": 
                                "function (doc) {\n  if (doc.type=='vessel') {\n    emit(doc.number, null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

        # DEVICE TABLE
        design_id = "_design/device"
        design_data = self.check_design(design_id, url)

        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_device": 
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'DEVICE_List') {\n    emit([doc.vessel_id, doc.device], null);\n  }\n}"
                            }
                    }
                }
            # self.db.save(design)
            self.insert_data(design)

        # MODULE TABLE
        design_id = "_design/module"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_module": 
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'DEVICE_Module') {\n    emit([doc.vessel_id, doc.module], null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

        # OPTION TABLE
        design_id = "_design/option"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_option": 
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'DEVICE_Option') {\n    emit([doc.vessel_id, doc.option], null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

        # VALUE TABLE
        design_id = "_design/value"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_value": 
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'DEVICE_Value') {\n    emit([doc.vessel_id, doc.device, doc.timestamp], null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

        # SYSTEM TABLE
        design_id = "_design/system"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_system": 
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'System') {\n    emit([doc.vessel_id, doc.timestamp], null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

        # INI TABLE
        design_id = "_design/ini"
        design_data = self.check_design(design_id, url)
        if 'error' in design_data.keys():
            design = {
                    "_id": design_id,
                    "views": {
                        "get_ini":
                            {"map": 
                                "function (doc) {\n  if (doc.type == 'INI') {\n    emit([doc.vessel_id, doc.timestamp], null);\n  }\n}"
                            }
                    }
                }
            self.insert_data(design)

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

    def exist_data(self, design, view, query, url=False):

        couch_query = self.couch_db_url()

        if url:
            couch_query = url
        
        couch_query += '_design/{0}/_view/{1}?{2}'.format(design, view, query)

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

    def get_id_exist_data(self, vessel_id, design, view, key, url=False):

        couch_query = self.couch_db_url()

        if url:
            couch_query = url

        query = 'startkey=["{0}","{1}"]'.format(vessel_id, key)
        query += '&endkey=["{0}","{1}"]'.format(vessel_id, key)
        couch_query += '_design/{0}/_view/{1}?{2}'.format(design, view, query)
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

    def insert_default(self, vessel_id, keys, column, table, view):
        view = 'get_' + view
        for key in keys:
            query = 'startkey=["{0}","{1}"]'.format(vessel_id, key)
            query += '&endkey=["{0}","{1}"]'.format(vessel_id, key)
            if not self.exist_data(column, view, query):

                # SAVE TO COUCH DATABASE
                doc = {
                    "type": table,
                    "vessel_id": vessel_id,
                    column: key
                }
                # SEVE TO COUCH DB
                self.insert_data(doc)

    def insert_not_exist(self, vessel_id, keys, column, table):

        datas = {}
        for key in keys:
            view = 'get_' + column
            key_id = self.get_id_exist_data(str(vessel_id), column, view, key)
            if not key_id:

                # SAVE TO COUCH DATABASE
                doc = {
                    "type": table,
                    "vessel_id": vessel_id,
                    column: key
                }

                # SEVE TO COUCH DB
                self.insert_data(doc)
                
                #  GET ID
                key_id = self.get_id_exist_data(str(vessel_id), column, view, key)
            if key_id:
                datas[key] = key_id[0]['id']

        return datas

    def insert_vessel(self, vessel_number, db=None, vessel_id=None):

        # SET VESSEL DATA
        doc = {
            "number": vessel_number,
            "type": "vessel"
        }

        # SAVE TO COUCH
        self.insert_data(doc)

    def write_default_values(self, INI, result, uniqueTable = None):

        self.vessel_number = INI.getOption("INFO","IMO")
        timestamp = time.time()

        if not self.get_vessel(self.vessel_number):
            self.insert_vessel(self.vessel_number)

        # VESSEL ID
        vessel_id = self.get_vessel(self.vessel_number)[0]['id']

        # DEVICE
        column = 'device'
        table = 'DEVICE_List'
        keys = ["PARAMETERS", "COREVALUES", "FAILOVER", "NTWCONF"]
        self.insert_default(vessel_id, keys, column, table, 'device')

        # MODULE
        column = 'module'
        table = 'DEVICE_Module'
        keys = ["General", "INFO"]
        self.insert_default(vessel_id, keys, column, table, 'module')

        # OPTION
        column = 'option'
        table = 'DEVICE_Option'
        keys = ["Update", "VESSELNAME"]
        self.insert_default(vessel_id, keys, column, table, 'option')

        deviceList = []
        moduleList = []
        optionList = []
        # workingDict = {}

        # print("result: ", json.dumps(result))
        for deviceName in result:
            for deviceNumber in result[deviceName]:
                if deviceNumber == 0:
                    completeName = deviceName
                else:
                    completeName = deviceName + str(deviceNumber)
                deviceList.append(completeName)
                for Module in result[deviceName][deviceNumber]:
                    if Module.lower() != "_extractinfo":
                        if not Module in moduleList:
                            moduleList.append(Module)
                        for option in result[deviceName][deviceNumber][Module]:
                            if not option in optionList:
                                optionList.append(option)

        try:
            
            self.INI = INI
            #check for empty result
            if result == None or result == {}:
                self.log.printError("Empty data can not be written into COUCH")
                self.log.printError("--> Given Data ignored!")
                return
            if self.Error == False:

                self.insert_not_exist(vessel_id, moduleList, "module", "DEVICE_Module")
                self.insert_not_exist(vessel_id, optionList, "option", "DEVICE_Option")
                self.insert_not_exist(vessel_id, deviceList, "device", "DEVICE_List")
                # Save Result
                if not uniqueTable:
                    print("None")
                    self.system_info(vessel_id, timestamp)
                    self.ini_update(vessel_id, timestamp)
                    self.save_result(vessel_id, result, timestamp)

                elif uniqueTable.upper() == "FAILOVER" or uniqueTable.upper() == "PARAMETERS":
                    print(uniqueTable.upper())
                    self.save_result(vessel_id, result, timestamp)

                return 1

        except Exception as e:
            raise
            self.Error = True
            self.log.printError("Local Database Processing Failed")

    def get_max_local_ids(self, column, vessel_id, query=None):

        couch_query = self.couch_db_url()

        if not query == None:
            couch_query = query

        couch_query += '_design/' + column + '/_view/get_' + column + '?'
        couch_query += 'startkey=["' + vessel_id + '",1,"\ufff0"]&endkey=["' + vessel_id + '",1]&'
        couch_query += 'descending=true&limit=1'

        # EXECUTE COUCH QUERY
        res = requests.get(couch_query)
        json_data = res.json()
        json_data = json_data['rows']

        # CHECK IF VESSEL EXIST
        if json_data:
            if json_data[0]['id']:
                return json_data[0]['id']
            else: return 0
        else:
            return 0

    def save_result(self, vessel_id, datas, timestamp):
        # print("datas: ", json.dumps(datas))
        for device in datas:
            values = {}

            for number in datas[device]:
                dev_name = device
                
                if number not in [0, '0']:
                    dev_name += str(number)

                values[dev_name] = datas[device][number]

                column = 'value'
                view = 'get_' + column
                device_info = self.get_value(vessel_id, column, view, dev_name)

                doc = {}

                if not device_info:

                    doc['vessel_id'] = vessel_id
                    doc['type'] = "DEVICE_Value"
                    doc['device'] = dev_name
                    doc['timestamp'] = timestamp
                    doc['value'] = values
                    self.insert_data(doc)

                else:

                    try:

                        del device_info['value'][dev_name]['_ExtractInfo']
                        del values[dev_name]['_ExtractInfo']

                    except:

                        pass

                    # if not device_info['value'] == values:

                    new_data = merge(device_info['value'], values)

                    doc['vessel_id'] = vessel_id
                    doc['type'] = "DEVICE_Value"
                    doc['device'] = dev_name
                    doc['timestamp'] = timestamp
                    doc['value'] = new_data
                    self.insert_data(doc)


    def get_value(self, vessel_id, design, view, key, url=False):

        couch_query = self.couch_db_url()

        if url:
            couch_query = url

        query = 'startkey=["' + vessel_id + '","' + key + '",0]'
        query += '&endkey=["' + vessel_id + '","' + key + '",{}]'

        couch_query += '_design/' + design + '/_view/' + view + '?' + query
        couch_query += '&include_docs=true'

        # EXECUTE COUCH QUERY
        res = requests.get(couch_query)
        json_data = res.json()
        json_data = json_data['rows']

        # CHECK IF VESSEL EXIST
        if json_data:
            if json_data[0]['id']:
                return json_data[0]['doc']
            else: return 0
        else:
            return 0

    def system_info(self, vessel_id, timestamp):
        start_time = 0
        end_time = 0
        # FIRST TIMESTAMP
        couch_query = self.couch_db_url()
        couch_query += "_design/value/_view/get_value?"
        couch_query += "startkey=[\"{0}\", \"COREVALUES\",0]".format(vessel_id)
        couch_query += "&endkey=[\"{0}\", \"COREVALUES\",9999999999]".format(vessel_id)
        couch_query += "&include_docs=true&limit=1"
        r = requests.get(couch_query)

        json_data = r.json()

        if json_data['rows']:
            start_time = json_data['rows'][0]['key'][2]

        # LAST TIMESTAMP
        couch_query = self.couch_db_url()
        couch_query += "_design/value/_view/get_value?"
        couch_query += "startkey=[\"{0}\", \"COREVALUES\",9999999999]".format(vessel_id)
        couch_query += "&endkey=[\"{0}\", \"COREVALUES\",0]".format(vessel_id)
        couch_query += "&include_docs=true&limit=1&descending=true"

        r = requests.get(couch_query)

        json_data = r.json()

        if json_data['rows']:
            end_time = json_data['rows'][0]['key'][2]

        # DB INFO
        couch_query = self.couch_db_url()

        r = requests.get(couch_query)

        json_data = r.json()

        if start_time and end_time:

            data = {}
            data["db_name"] = json_data["db_name"]
            data["sizes"] = json_data["sizes"]
            data["other"] = json_data["other"]
            data["doc_count"] = json_data["doc_count"]
            data["doc_del_count"] = json_data["doc_del_count"]
            data["disk_size"] = json_data["disk_size"]
            data["disk_format_version"] = json_data["disk_format_version"]
            data["data_size"] = float(json_data["data_size"]) / 1000000
            data["start_time"] = start_time
            data["end_time"] = end_time
            data["backend_version"] = self.current_branch(self.backend_dir)
            data["ui_version"] = self.current_branch(self.web_dir)
            data["api_version"] = self.current_branch(self.api_dir)

            doc = {}
            doc['vessel_id'] = vessel_id
            doc['type'] = "System"
            doc['data'] = data
            doc['timestamp'] = timestamp
            self.insert_data(doc)

            return 1

        return 0

    def get_file_content(self, fdir, fname):
        filename = fdir + fname

        with open(filename, 'r') as theFile:
            data = theFile.read().splitlines()

            return data

        return []

    def ini_update(self, vessel_id, timestamp):

        # GET LAST DATA
        couch_query = self.couch_db_url()
        couch_query += "_design/ini/_view/get_ini?"
        couch_query += "startkey=[\"{0}\", 9999999999]".format(vessel_id)
        couch_query += "&endkey=[\"{0}\", 0]".format(vessel_id)
        couch_query += "&include_docs=true&limit=1&descending=true"
        r = requests.get(couch_query)

        json_data = r.json()

        app_dir = "/home/rh/backendv1/"
        ini_files = ["SYSTEM.INI", "ini/CONFIG.INI", "ini/COMPLEXCONFIG.INI",
                     "ini/NETWORK.INI", "ini/PORTFORWARDING.INI", "ini/FIREWALL.INI",
                     "ini/EMGFAILOVER.INI"]

        datas = {}

        for ini_file in ini_files:

            content = {}
            content['content'] = self.get_file_content(app_dir, ini_file)
            content['dir'] = ini_file

            datas[ini_file.split("ini/")[-1]] = content

        # VALIDATE DATE SAVE IF CHANGE HAPPEN
        change_flag = False

        try:

            if json_data["rows"]:

                curren_data = json_data["rows"][0]["doc"]

                if curren_data:

                    for key in datas.keys():

                        if not curren_data['data'][key]['content'] == datas[key]['content']:
                            change_flag = True

                        ini_dir = app_dir + curren_data['data'][key]['dir']
                        mtime = os.path.getmtime(ini_dir)

                        if int(curren_data['timestamp']) < int(mtime):
                            change_flag = True

            else:

                change_flag = True

        except:

            print("Initial data INI Files for Couch!!!")

        if change_flag:

            print("Update INI file database!")
            doc = {}
            doc['vessel_id'] = vessel_id
            doc['type'] = "INI"
            doc['data'] = datas
            doc['timestamp'] = int(timestamp)

            self.insert_data(doc)

        return 1

    def current_branch(self, dir):

        command = "cd " + dir + ";git branch | grep \* | cut -d ' ' -f2"

        return self.run_commands(command)

    def run_commands(self, command):

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
        output, _ = process.communicate()

        return output.decode('ascii')
