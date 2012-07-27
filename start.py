#!/usr/bin/env python
""""Server entry point."""

import logging 
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.options import define, options

from wdcnz import application

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

define("port", default=8888, help="run on the given port", type=int)
define("cassandra_host", default="localhost:9160", 
    help="Cassandra host and port.")
define("cassandra_keyspace", default="wdcnz", help="Cassandra Keyspace")
        
def main():
    
    log.info("Starting...")
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(
        application.WdcnzApplication())
    http_server.listen(options.port)
    log.info("Staring IO Loop")
    tornado.ioloop.IOLoop.instance().start()
    log.info("IO Loop stopped")
    return
    
if __name__ == "__main__":
    main()
    