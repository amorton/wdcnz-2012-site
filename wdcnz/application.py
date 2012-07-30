""""Application Entry Point"""
import os

import pycassa

import tornado.web
from tornado.options import options

from wdcnz import controllers

class WdcnzApplication(tornado.web.Application):
    def __init__(self):
        
        handlers = [
            (r"/", controllers.Home),
            (r"/tweets", controllers.Tweets),
            (r"/tweets/deleted", controllers.DeletedTweets),
            
            (r"/users/([^/]+)/?", controllers.User),
            (r"/users/([^/]+)/followers/?", controllers.UserFollowers),
            (r"/users/([^/]+)/not_followers/?", controllers.UserNotFollowers),
                                    
            (r"/login", controllers.Login),
            (r"/logout", controllers.Logout),
            (r"/signup", controllers.Signup),
            
        ]
        
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url="/auth/login",
            autoescape=None,
            cookie_secret="A cromulent secret embiggens the smallest demo",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
        self.cass_pool = pycassa.ConnectionPool(
            options.cassandra_keyspace, 
            options.cassandra_host.split(","))


        return
