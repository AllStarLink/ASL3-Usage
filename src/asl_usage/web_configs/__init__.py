#!/usr/bin/python3
#
# Copyright(C) 2023-2024 AllStarLink
# ASL3-Usage and all components are Licensed under the AGPLv3
# see https://raw.githubusercontent.com/AllStarLink/ASL3-Usage/develop/LICENSE
#

import configparser
import logging
import re
import sys

_BUILD_ID = "@@HEAD-DEVELOP@@"
log = logging.getLogger(__name__)

class WebConfigs:
    def __init__(self, config_file):

        config = configparser.ConfigParser()
        config.read(config_file)

        if "USERS_TABLE_LOCATION" in config["web"]:
            self.user_table = re.sub(r'[\'\"]', '', config["web"]["USERS_TABLE_LOCATION"])
        else:
            self.user_table = "/etc/asl-usage/users"

        if "HTTP_PORT" in config["web"]:
            self.http_port = config["web"]["HTTP_PORT"]
        else:
            self.http_port = 16080
        log.info("ASL3-Usage Master HTTP port is %s", self.http_port)

        if "HTTP_BIND_ADDR" in config["web"]:
            self.http_bind_addr = str(config["web"]["HTTP_BIND_ADDR"])
            log.info("Binding services to %s", self.http_bind_addr)
        else:
            self.http_bind_addr = None
            log.info("Binding sevices to all addresses")

        if "DB_HOST" in config["web"]:
            self.db_host =  str(config["web"]["DB_HOST"])
        else:
            self.http_bind_addr = "localhost"
        log.info("Database host: %s", self.db_host)

        if "DB_PORT" in config["web"]:
            self.db_port = int(config["web"]["DB_PORT"])
        else:
            self.db_port = 3306
        log.info("Database port: %s", self.db_port)

        if "DB_USER" in config["web"]:
            self.db_user =  str(config["web"]["DB_USER"])
        else:
            self.db_user = "localhost"
        log.info("Database user: %s", self.db_user)

        if "DB_PASS" in config["web"]:
            self.db_pass =  str(config["web"]["DB_PASS"])
        else:
            self.db_pass = "aslusage"

        if "DB_DB" in config["web"]:
            self.db_db =  str(config["web"]["DB_DB"])
        else:
            self.db_db = "aslusage"
        log.info("Database database: %s", self.db_host)

class WebConfigsException(Exception):
    """ Exception for ASLNodeConfig{,s} """
