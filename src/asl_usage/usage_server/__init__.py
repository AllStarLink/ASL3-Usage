#!/usr/bin/python3
#
# Copyright(C) 2023-2024 AllStarLink
# ASL3-Usage and all components are Licensed under the AGPLv3
# see https://raw.githubusercontent.com/AllStarLink/ASL3-Usage/develop/LICENSE
#

import asyncio
import base64
import datetime
from itertools import cycle
import json
import logging
import pprint
import re
import time
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

        is_successful = True
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
    
            pprint.pp(data["nodes"])
            for node in data["nodes"]:
                log.debug(f"processing node {node}")
                if str(node) in self.nodedb.node_database:
                    log.debug(f"{node} in node_database")
                    channeltype = data["nodes-channels"][str(node)]
                    sql = """REPLACE INTO nodes
                        (uuid, astversion, aslversion, aslpkgver, node, uptime,
                        reloadtime, channeltype, os, distro, relver, kernel,
                        arch, pkglist, fullastver)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                    values = (data["uuid"], astversion, aslversion, aslpkgver, node, uptime,
                        reloadtime, channeltype, data["os"], data["distro"], data["release"],
                        data["kernel"], arch, pkglist, data["ast-ver"])

                    async with self.db.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(sql, values)
                            await conn.commit()
    
                else:
                    log.error(f"usage received for {node} but not in node_database; discarding")
                    is_successful = False

        except Exception as e:
            log.error(e)
            return web.Response(status=404)

        if is_successful:
            return web.Response(status=200)
        else:
             return web.Response(status=503)
    ##
    ## Reports
    ##

    async def quick_select(self, sql_txt):
        try:
            async with self.db.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql_txt);
                    return await cur.fetchall()
        except Exception as e:
            log.error(e)
            return None

    async def quick_select_single(self, sql_txt):
        try:
            r = await self.quick_select(sql_txt)
            return str(r[0][0])
        except Exception as e:
            log.error(e)
            return None
            
    async def proc_reports(self, request):
        r_txt = None
        try:
            c = request.url.path.split("/")
            if c[2] == "basic" or c[2] == "basic/":
                sql = "SELECT COUNT(DISTINCT uuid) FROM nodes"
                r = await self.quick_select_single(sql)
                r_txt = f"{'Distinct Servers':>20}: {r:>4}\n"
                sql = "SELECT COUNT(DISTINCT node) FROM nodes"
                r = await self.quick_select_single(sql)
                r_txt += f"{'Distinct Nodes':>20}: {r:>4}\n\n"
    
                r_txt += f"{'Channel Types':>20}\n"
                sql = "SELECT channeltype, COUNT(channeltype) FROM nodes GROUP BY channeltype"
                rows = await self.quick_select(sql)
                for row in rows:
                    r_txt += f"{row[0]:>20}: {row[1]:>4}\n"

            elif c[2] == "dump" or c[2] == "dump/":
                sql = """SELECT repdate,node,fullastver,channeltype,
                    SEC_TO_TIME(uptime), SEC_TO_TIME(reloadtime), uuid
                    FROM nodes ORDER BY repdate DESC, node ASC;
                    """
                rows = await self.quick_select(sql)
               
                r_txt =   "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n" 
                r_txt += f" {'Report In Time':<20}| {'Node':<8}| {'Version':<36}| {'Channel Type':<20}| {'Uptime':<20}| {'Reload Time':<20}| {'UUID':<37}\n"
                r_txt +=  "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n"

                for r in rows:
                    rit = r[0].strftime("%Y-%m-%d %H:%M:%S %Z")
                    ut = str(r[4])
                    rt = str(r[5])
                    r_txt += f" {rit:<20}| {r[1]:<8}| {r[2]:<36}| {r[3]:<20}| {ut:<20}| {rt:<20}| {r[6]:<37}\n"

                r_txt +=  "-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n"

            elif c[2] == "daily" or c[2] == "daily/":
                sql = "SELECT * FROM asl_usage ORDER BY collected_time DESC"
                rows = await self.quick_select(sql)

                r_txt =   "-------------------------------------------------------------------------------------------------------------------------------------------------\n"
                r_txt += f" {'Collected':<20} | {'Node Cnt':<9}| {'Server Cnt':<10}| {'SimpleUSB Cnt':<14}| {'USBRadio Cnt':<13}| {'DAHDI Cnt':<10}| {'Voter Cnt':<10}| {'Radio Cnt':<10}| {'Diff Ast Ver':<13}| {'Diff ASL Ver':<13}\n"
                r_txt +=  "-------------------------------------------------------------------------------------------------------------------------------------------------\n"

                for r in rows:
                    cit = r[10].strftime("%Y-%m-%d %H:%M:%S")
                    r_txt += f" {cit:>20} | {r[5]:>9}| {r[2]:>9} | {r[7]:>13} | {r[8]:>12} | {r[6]:>9} | {r[9]:>9} | {r[11]:>9} | {r[3]:>12} | {r[4]:>12}\n"

                r_txt +=  "-------------------------------------------------------------------------------------------------------------------------------------------------\n"

        except (IndexError, KeyError):
            log.debug("IndexError/KeyError")
            r_txt = None

        except Excpetion as e:
            log.error(e)

        finally:
            if r_txt:
                return web.Response(text=r_txt, content_type="text/plain")
 
            return web.Response(text="503: an error occurred", content_type="text/plain", status=503)



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
