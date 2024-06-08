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
import pprint
import re
import time
import websockets
from aiohttp import web
from aiohttp_session import get_session, setup
from aiohttp_session import SimpleCookieStorage
import aiomysql
from .. import security, web_configs, node_db

__BUILD_ID = "@@HEAD-DEVELOP@@"
log = logging.getLogger(__name__)

class UsageServer:
    """ Node command WS client """

    __MAX_MSG_LEN = 256

    def __init__(self, configs_web, server_security, db_pool, node_db):
        self.config_web = configs_web
        self.server_security = server_security
        self.db = db_pool
        self.nodedb = node_db

    @staticmethod
    def get_json_error(message):
        return f"{{ \"ERROR\" : \"{message}\" }}"

    @staticmethod
    def get_json_success(message):
        if re.match(r'^[\{\[]', message):
            return f"{{ \"SUCCESS\" : {message} }}"
        return f"{{ \"SUCCESS\" : \"{message}\" }}"

    @staticmethod
    def get_json_security(message):
        return f"{{ \"SECURITY\" : \"{message}\" }}"

    ##
    ## Security Auth Functions
    ##
    async def proc_auth(self, request):
        try:
            c = request.url.path.split("/")
            r_json = None
            if c[2] == "check":
                session = await get_session(request)
                session["last_auth_check"] = time.time()
                r_json = self.get_json_security("No Session")
                if "auth_sess" in session:
                    if session["auth_sess"] in self.server_security.session_db:
                        r_json = self.get_json_success("Logged In")

            elif c[2] == "logout":
                session = await get_session(request)
                session["auth_sess"] = "" 
                r_json = self.get_json_security("No Session")

        except (IndexError, KeyError):
            log.debug("IndexError/KeyError")
            r_txt = None

        finally:
            if r_json:
                return web.Response(text=r_json, content_type="text/json")
    
            return web.Response(status=400)

    async def proc_login(self, request):
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
            r_txt = self.get_json_success("OK")
            log.info("successful login by user %s from %s", 
                req.get("user"), client_ip)
        else:
            r_txt = self.get_json_security("invalid user or pass")
            session["auth_sess"] = None
            log.info("invalid login %s:%s from %s", 
                req.get("user"), req.get("pass"), client_ip)

        return web.Response(text=r_txt, content_type="text/json")

    ##
    ## Usage POSTs
    ##
    async def proc_usage(self, request):
        try:
            req = await request.text()
            data = json.loads(req)

            # Parse versions
            fullver = data["ast-ver"]
            parsed_ver = re.search(r"^(\S+)\s+([0-9.]+)\+(.*\-.*)\-(.*)$", fullver)
            if parsed_ver:
                astversion = parsed_ver.group(2)
                aslversion = parsed_ver.group(3)
                aslpkgver = parsed_ver.group(4)

            # h:m:s to s
            uptime = int(data["uptime"])
            reloadtime = int(data["reload-time"])

            if( data["arch"] == "aarch64" ):
                arch = "arm64"
    
            if( data["arch"] == "x86_64" ):
                arch = "amd64"

            pkglist = json.dumps(data["pkgs"])
    
            for node in data["nodes"]:
                if str(node) in self.nodedb.node_database:
                    log.debug("in")
                    channeltype = data["nodes-channels"][str(node)]
                    sql = f"""REPLACE INTO nodes
                            (uuid, astversion, aslversion, aslpkgver, node, uptime,
                            reloadtime, channeltype, os, distro, relver, kernel,
                            arch, pkglist, fullastver)
                            VALUES(
                                '{data["uuid"]}', '{astversion}', '{aslversion}', '{aslpkgver}',
                                {node}, {uptime}, {reloadtime}, '{channeltype}', 
                                '{data["os"]}', '{data["distro"]}', '{data["release"]}',
                                '{data["kernel"]}', '{arch}', '{pkglist}', '{data["ast-ver"]}'
                            )
                        """
                    async with self.db.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(sql)
                            await conn.commit()
    
                    return web.Response(status=200)    
                else:
                    log.debug("false")
                    return web.Response(status=403)

        except Exception as e:
            log.error(e)
            return web.Response(status=404)
    ##
    ## Reports
    ##
    async def proc_reports(self, request):
        try:
            c = request.url.path.split("/")
            r_txt = None
            if c[2] == "basic":
                async with self.db.acquire() as conn:
                    async with conn.cursor() as cur:
                        sql = "SELECT COUNT(DISTINCT uuid) AS node_count FROM nodes"
                        await cur.execute(sql)
                        r = await cur.fetchall()
                        r_txt = f"UUIDs: {r[0]}"

                
        except (IndexError, KeyError):
            log.debug("IndexError/KeyError")
            r_txt = None

        except Excpetion as e:
            log.error(e)

        finally:
            if r_txt:
                return web.Response(text=r_txt, content_type="text/plain")
    
            return web.Response(status=400)



    ##
    ## Server Logic
    ##
    async def main(self):

        # setup base server
        httpserver = web.Application()
        setup(httpserver, SimpleCookieStorage())

        # Handlers for different API commands
        api_routes = [
            web.post("/login", self.proc_login),
            web.get(r"/auth/{cmd:.*}", self.proc_auth),
            web.post("/usage", self.proc_usage),
            web.get(r"/reports/{cmd:.*}", self.proc_reports)
            ]
        httpserver.add_routes(api_routes)
        
        runner = web.AppRunner(httpserver)
        await runner.setup()
        site = web.TCPSite(runner, 
            self.config_web.http_bind_addr,
            self.config_web.http_port)
        await site.start()


class UsageServerException(Exception):
    """ specific Exception for class """
