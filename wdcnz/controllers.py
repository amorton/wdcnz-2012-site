"""Controllers for page endpoints"""

import tornado.web

class ControllerBase(tornado.web.RequestHandler):
    pass

class Splash(ControllerBase):
    
    def get(self):
        self.write("howdy")
        return
        