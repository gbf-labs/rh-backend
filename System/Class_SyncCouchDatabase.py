import lib_Log
import lib_config
import lib_CouchDB
import Class_GIT
import couchdb
import requests
import json
import time
import re
import subprocess

import sys

class SyncCouchDatabase():

    def __init__(self, INI):

        self.INI = INI

        self.vessel_number = INI.getOption("INFO","IMO")

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

        self.remote_couch_protocol = config_data.remote_couch_protocol
        self.remote_couch_user = config_data.remote_couch_user
        self.remote_couch_password = config_data.remote_couch_password
        self.remote_couch_host = config_data.remote_couch_host
        self.remote_couch_port = config_data.remote_couch_port
        self.remote_db_name = config_data.remote_db_name

        self.log = lib_Log.Log(PrintToConsole = True)

    def couch_db_url(self, design=None):

        couch_query = self.couch_protocol + '://'+ self.couch_user 
        couch_query += ':' + self.couch_password + '@' + self.couch_host 
        couch_query += ':' + self.couch_port
        couch_query += '/' + self.couchdb_name + '/'

        if design:
            couch_query += design

        return couch_query

    def remote_couch_db_url(self, design=None):

        remote = self.remote_couch_protocol + '://'+ self.remote_couch_user 
        remote += ':' + self.remote_couch_password + '@' + self.remote_couch_host 
        remote += ':' + self.remote_couch_port
        remote += '/' + self.remote_db_name + '/'

        if design:
            remote += design

        return remote

    def SyncDatabase(self):

        self.log.mainTitle ("SYNC DATA")
        vessel_id = self.get_vessel(self.vessel_number)[0]['id']

        values = self.get_complete_values(
            vessel_id,
            "FAILOVER",
            flag='one_doc'
        )

        if not values: return 0

        policy = str(values['value']['FAILOVER']['General']['Policy'])

        if policy == 'POL_ALLOWALL':

            self.log.printInfo("POL_ALLOWALL Policy!")
            couch_query = self.remote_couch_protocol + '://'+ self.remote_couch_user 
            couch_query += ':' + self.remote_couch_password + '@' + self.remote_couch_host 
            couch_query += ':' + self.remote_couch_port
            couch_query += '/' + self.remote_db_name + '/_design/vessel/_view/get_vessels'

            json_data = {}
            for count in range(0, 5):

                try:
                    self.log.printInfo("Checking connection...")
                    res = requests.get(couch_query)
                    json_data = res.json()
                    self.log.printInfo("Connection stable!")
                except:
                    self.log.printWarning("Can't connect to remote database, Try to connect again after 5 seconds.")
                    time.sleep(5)
                else:
                    break
                
                if count == 4:
                    self.log.printError ("Can't connect to Remote Database!")
                    return 0

            rows = json_data['rows']

            duplicate = False
            for row in rows or []:

                if row['key'] == self.vessel_number and row['id'] != vessel_id:

                    duplicate = True
                    self.log.printWarning("Sync is not possible, production already have the same Vessel IMO!")

            if not duplicate:

                # CREATE REPLICATOR DB
                replicator_db = self.couch_protocol + '://'+ self.couch_user 
                replicator_db += ':' + self.couch_password + '@' + self.couch_host 
                replicator_db += ':' + self.couch_port
                replicator_db += '/_replicator/'

                headers = {"Content-Type" : "application/json"}

                requests.put(replicator_db, headers=headers)

                # REPLICATE
                url = self.couch_protocol + '://'+ self.couch_user 
                url += ':' + self.couch_password + '@' + self.couch_host 
                url += ':' + self.couch_port
                # url += '/' + '_replicate'
                url += '/' + '_replicator'

                source = self.couch_protocol + '://'+ self.couch_user 
                source += ':' + self.couch_password + '@' + self.couch_host 
                source += ':' + self.couch_port
                source += '/' + self.couchdb_name + '/'

                target = self.remote_couch_protocol + '://'+ self.remote_couch_user 
                target += ':' + self.remote_couch_password + '@' + self.remote_couch_host 
                target += ':' + self.remote_couch_port
                target += '/' + self.remote_db_name + '/'

                data = {}
                data["source"] = source
                data["target"] = target
                data["create_target"] = True
                data["continuous"] = False

                headers = {"Content-Type" : "application/json"}
                self.log.printInfo("Init syncing data!")
                
                try:
                    requests.post(url, data=json.dumps(data),headers=headers)
                except:
                    self.log.printError("Can't connect to Remote Database!")

                self.log.printInfo("Syncing data!")

        elif policy == 'POL_VSAT':

            self.log.printInfo("POL_VSAT Policy!")
            device_list = self.get_device(vessel_id)
            for device in device_list:

                if device['device'] in ['PARAMETERS', 'COREVALUES', 'FAILOVER', 'NTWCONF', 'NTWPERF1']:

                    self.sync_data(device['device'], vessel_id)

                if  re.findall(r'VSAT\d', device['device']):

                    self.sync_data(device['device'], vessel_id)

        elif policy == 'POL_FBB':

            self.log.printInfo("POL_FBB Policy!")
            device_list = self.get_device(vessel_id)
            for device in device_list:
                
                if device['device'] in ['PARAMETERS', 'COREVALUES', 'FAILOVER', 'NTWCONF', 'NTWPERF1']:

                    self.sync_data(device['device'], vessel_id)

                if  re.findall(r'Modem\d', device['device']):

                    self.sync_data(device['device'], vessel_id)

                elif  re.findall(r'VSAT\d', device['device']):

                    self.sync_data(device['device'], vessel_id)

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


    # REMOVE KEY
    def remove_key(self, data, item):

        # CHECK DATA
        if item in data:

            # REMOVE DATA
            del data[item]

        # RETURN
        return data

    def insert_data(self, data, design=None):

        url = self.remote_couch_db_url(design)

        headers = {"Content-Type" : "application/json"}
        r = requests.post(url, data=json.dumps(data),headers=headers)

        json_data =   r.json()
        return json_data

    def sync_data(self, device, vessel_id):
    
        remote = self.remote_couch_protocol + '://'+ self.remote_couch_user 
        remote += ':' + self.remote_couch_password + '@' + self.remote_couch_host 
        remote += ':' + self.remote_couch_port
        remote += '/' + self.remote_db_name 

        remote_values = self.get_complete_values(
            vessel_id,
            device,
            flag='one_doc',
            remote=remote
        )

        if not remote_values:
            # VESSEL IS NOT YET SYNC
            self.log.printWarning("Nothing to sync! Policy needs to be POL_ALLOWALL first!")
            return 0

        values = self.get_complete_values(
            vessel_id,
            device,
            str(float(remote_values['timestamp'])),
            str(time.time()),
            flag='all'
        )

        for value in values:

            final_value = self.remove_key(value,"_rev")

            self.insert_data(final_value)

    def get_device(self, vessel_id, limit=1000000, flag=False):

        couch_query = self.couch_db_url()
        couch_query += '/_design/device/_view/get_device?'
        couch_query += 'startkey=["' + vessel_id + '"]&'
        couch_query += 'endkey=["' + vessel_id + '",{}]'
        couch_query += '&include_docs=true'

        res =         requests.get(couch_query)
        json_data =   res.json()
        rows =   json_data['rows']

        data = []
        for row in rows:

            data.append(row['doc'])

        return data