#!/usr/bin/python3
#
# Copyright(C) 2023-2024 AllStarLink
# ASL3-Usage and all components are Licensed under the AGPLv3
# see https://raw.githubusercontent.com/AllStarLink/ASL3-Usage/develop/LICENSE
#

import asyncio
import base64
from itertools import cycle
import json
import logging
import re
import time
import websockets
from aiohttp import web
from aiohttp_session import get_session, setup
from aiohttp_session import SimpleCookieStorage
from .. import security, web_configs

__BUILD_ID = "@@HEAD-DEVELOP@@"
log = logging.getLogger(__name__)

class UsageServer:
    """ Node command WS client """

    __MAX_MSG_LEN = 256

    def __init__(self, configs_web, server_security):
        self.config_web = configs_web
        self.httpserver = web.Application()
        self.server_security = server_security

    @staticmethod
    def __get_json_error(message):
        return f"{{ \"ERROR\" : \"{message}\" }}"

    @staticmethod
    def __get_json_success(message):
        if re.match(r'^[\{\[]', message):
            return f"{{ \"SUCCESS\" : {message} }}"
        return f"{{ \"SUCCESS\" : \"{message}\" }}"

    @staticmethod
    def __get_json_security(message):
        return f"{{ \"SECURITY\" : \"{message}\" }}"

    ##
    ## Security Auth Functions
    ##
    async def __proc_auth(self, request):
        try:
            c = request.url.path.split("/")
            r_json = None
            if c[2] == "check":
                session = await get_session(request)
                session["last_auth_check"] = time.time()
                r_json = self.__get_json_security("No Session")
                if "auth_sess" in session:
                    if session["auth_sess"] in self.server_security.session_db:
                        r_json = self.__get_json_success("Logged In")

            elif c[2] == "logout":
                session = await get_session(request)
                session["auth_sess"] = "" 
                r_json = self.__get_json_security("No Session")

        except (IndexError, KeyError):
            log.debug("IndexError/KeyError")
            r_txt = None

        finally:
            if r_json:
                return web.Response(text=r_json, content_type="text/json")
    
            return web.Response(status=400)

    async def __proc_login(self, request):
        req = await request.post()
        session = await get_session(request)

        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers.get("X-Forwarded-For")
        else:
            client_ip = request.remote

        is_valid = self.server_security.validate(req.get("user"), req.get("pass"))
        if is_valid:
            session_id = self.server_security.create_session(client_ip, req.get("user"))
            session["auth_sess"] = session_id
            r_txt = self.__get_json_success("OK")
            log.info("successful login by user %s from %s", 
                req.get("user"), client_ip)
        else:
            r_txt = self.__get_json_security("invalid user or pass")
            session["auth_sess"] = None
            log.info("invalid login %s:%s from %s", 
                req.get("user"), req.get("pass"), client_ip)

        return web.Response(text=r_txt, content_type="text/json")

    ##
    ## Server Logic
    ##
    async def main(self):

        # Session
        setup(self.httpserver, SimpleCookieStorage())

        # Handlers for different API commands
        api_routes = [
            web.post("/login", self.__proc_login),
            web.get(r"/auth/{cmd:.*}", self.__proc_auth),
            ]
        self.httpserver.add_routes(api_routes)
        runner = web.AppRunner(self.httpserver)
        await runner.setup()
        site = web.TCPSite(runner, 
            self.config_web.http_bind_addr,
            self.config_web.http_port)
        await site.start()


class UsageServerException(Exception):
    """ specific Exception for class """
