#!/usr/bin/python3
#
# Copyright(C) 2023-2024 AllStarLink
# ASL3-Usage and all components are Licensed under the AGPLv3
# see https://raw.githubusercontent.com/AllStarLink/ASL3-Usage/develop/LICENSE
#

import logging
import re
import time
import urllib.request
import asyncio
import aiohttp

_BUILD_ID = "@@HEAD-DEVELOP@@"
log = logging.getLogger(__name__)

class ASLNodeDB:
    """ AllStarLink Node Dadabase """
    
    __url = "https://allmondb.allstarlink.org/"

    def __init__(self):
        self.node_database = {}
        
    # Read and load in the ASL Database
    async def get_allmon_db(self):
        log.debug("entering get_allmon_db()")
        retries = 0
        db_text = ""
        while retries < 5:
            try:
                log.info("Retrieving database from %s", self.__url)
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.__url) as resp:
                        db_text = await resp.text()
                retries = 255
            except aiohttp.ClientConnectorError as e:
                log.error(e)
            except Exception as e:
                log.error("Failed to retrieve database with error: %s", e)

            if retries != 255:
                retries += 1
                log.info("Will retry %d/5 in 5m", retries)
                await asyncio.sleep(300)

        if retries != 255:
            raise ASLNodeDBException("retrieval of database failed after 5 attempts")

        try:        
            nodedb = re.split(r"\n", db_text) 
    
            for ni in nodedb:
                r = re.split(r"\|", ni)
                if len(r) == 4:
                    self.node_database.update( { str(r[0]) : {} } )
                    self.node_database[str(r[0])].update( { "CALL" : r[1] , "DESC" : r[2] , "LOC" : r[3] } )
            elapsed_time = time.time() - start_time
        
            if len(self.node_database) < 2:
                log.error("Node file successfully retrieved but is empty or contains garbage")
            log.info("Updated node database in {0:.2f} seconds".format(elapsed_time))

        except Exception as e:
            log.error("Error processing nodedb after retrival: %s ", e)
            raise ASLNodeDBException(e) from e

        log.debug("exiting getAllMonDB()")
    
    async def full_update(self):
        log.debug("entering full_update")
        try:
            await self.get_allmon_db()
            log.info("populated AllStarlink database")
        except ASLNodeDBException as e:
            log.error(e)

    async def db_updater(self):
        await self.full_update()
        while True:
            await asyncio.sleep(15*60)
            await self.full_update()

class ASLNodeDBException(Exception):
    """ sepcific Exception for class """
