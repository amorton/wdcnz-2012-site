""""Application Entry Point"""
import os

import tornado.web

from wdcnz import controllers

class WdcnzApplication(tornado.web.Application):
    def __init__(self):
        
        handlers = [
            (r"/", controllers.Home),
            
            # (r"/auth/login", AuthLoginHandler),
            # (r"/auth/logout", AuthLogoutHandler),
        ]
        
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url="/auth/login",
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        return
