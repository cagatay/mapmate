from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.api import channel

'''
 Controller class
'''

class Controller(webapp.RequestHandler):

    def get(self, templateDict=None):
        return
    
    def post(self):
        args = simplejson.loads(self.request.body)
        
        func = args['func']
        del args['func']

        if func.startswith("_"):
            self.error(404)
        else:
            func = getattr(self, func)
            result = func(args)
            if result:
                self.writeJson(result)
        return
    
    def sendMessage(self, client_id, message):
        try:
            channel.send_message(client_id, simplejson.dumps(message))
        except:
            pass
        
    def writeJson(self, data):
        self.response.out.write(simplejson.dumps({
            'data': data
        }))
        return
