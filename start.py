""""Server entry point."""

import tornado.httpserver
import tornado.ioloop
import tornado.options

from tornado.options import define, options

from wdcnz import application

define("port", default=8888, help="run on the given port", type=int)
define("cassandra_host", default="localhost:9160", 
    help="Cassandra host and port.")
define("cassandra_keyspace", default="twitter", help="Cassandra Keyspace")
        
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(
        application.WdcnzApplication())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
    