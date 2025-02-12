#!/usr/bin/python3
#
# Copyright(C) 2023-2024 AllStarLink
# ASL3-Usage and all components are Licensed under the AGPLv3
# see https://raw.githubusercontent.com/AllStarLink/ASL3-Usage/develop/LICENSE
#

import csv
import logging
import re
import uuid
import time
import argon2

_BUILD_ID = "@@HEAD-DEVELOP@@"
log = logging.getLogger(__name__)

class Security:
    """ ASL3-Usage Security Subsystem """

    session_db = None
    userdb = None
    user_file = None

    def __init__(self, user_file):
        self.session_db = {}
        self.userdb = {}
        self.restricted_users = []
        self.restrictdb = []
        self.user_file = user_file
        self.__load_db()

    def __load_db(self):
        with open(self.user_file, newline="", encoding="utf-8") as uf:
            users = csv.DictReader(uf, delimiter="|")
            for row in users:
                self.userdb.update({ row["user"] : row["pass"] })
        log.debug("loaded %s entries from %s", len(self.userdb), self.user_file)
        uf.close()

    def reload_db(self):
        self.userdb.clear()
        self.session_db.clear()
        self.__load_db()

    def validate(self, user, passwd):
        try:
            if user == "user":
                log.debug("User passed as 'user'; auto-reject")
                return False
    
            if user in self.userdb:
                ph = argon2.PasswordHasher(type=argon2.Type.ID)
                ph.verify(self.userdb[user], passwd)
                return True
        
            return False
    
        except argon2.exceptions.VerifyMismatchError:
            return False

    def create_session(self, ipaddr, user):
        ss = SecuritySession(ipaddr, user)
        self.session_db.update({ ss.session_id : ss })
        return ss.session_id

    def destroy_session(self, session_id):
        try:
            self.session_db.pop(session_id)
            return True
        except (IndexError, KeyError):
            return False

class SecuritySession:
    """ Basically a stuct """
    def __init__(self, ipaddr, user):
        self.ipaddr = ipaddr
        self.user = user
        self.session_id = str(uuid.uuid4())
        self.creation = int(time.time())

class SecurityException(Exception):
    """ Exceptions for the Security class """
