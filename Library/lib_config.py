
import ConfigParser
from lib_config_parser import configSectionParser

class CONFIG_DATA():

    def __init__(self):
        
        # INIT CONFIG
        config = ConfigParser.ConfigParser()
        # CONFIG FILE
        config.read("config/config.cfg")

        # COUCH DATABASE NAME
        self.couchdb_name = configSectionParser(config,"COUCHDB")['db_name']

        # COUCH CREDENTIALS
        self.couch_protocol = configSectionParser(config,"COUCHDB")['protocol']
        self.couch_user = configSectionParser(config,"COUCHDB")['user']
        self.couch_password = configSectionParser(config,"COUCHDB")['password']
        self.couch_host = configSectionParser(config,"COUCHDB")['host']
        self.couch_port = configSectionParser(config,"COUCHDB")['port']

        # REMOTE COUCH CREDENTIALS
        self.remote_couch_protocol = configSectionParser(config,"RH_DB_SERVER")['protocol']
        self.remote_couch_user = configSectionParser(config,"RH_DB_SERVER")['user']
        self.remote_couch_password = configSectionParser(config,"RH_DB_SERVER")['password']
        self.remote_couch_host = configSectionParser(config,"RH_DB_SERVER")['host']
        self.remote_couch_port = configSectionParser(config,"RH_DB_SERVER")['port']
        self.remote_db_name = configSectionParser(config,"RH_DB_SERVER")['db_name']

        # INTERFACE
        self.interface = configSectionParser(config, "INTERFACE")['interface']

        # REPO_DIR
        self.backend_dir = configSectionParser(config, "REPO_DIR")['backend']
        self.api_dir = configSectionParser(config, "REPO_DIR")['api']
        self.web_dir = configSectionParser(config, "REPO_DIR")['web']

        # MONITORING
        self.monitoring = configSectionParser(config, "MONITORING")['enable']

        # BRANCH
        # INIT CONFIG
        branch_cfg = ConfigParser.ConfigParser()
        # CONFIG FILE
        branch_cfg.read("config/branch.cfg")

        try:

            self.web_branch = configSectionParser(branch_cfg,"BRANCH")['web']
            self.api_branch = configSectionParser(branch_cfg,"BRANCH")['api']
            self.backend_branch = configSectionParser(branch_cfg,"BRANCH")['backend']

        except:

            self.web_branch = ""
            self.api_branch = ""
            self.backend_branch = ""
