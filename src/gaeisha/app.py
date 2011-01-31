from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.api import channel

from urlparse import urlparse

'''
 Controller class
'''

class Controller(webapp.RequestHandler):
    def get(self):
        self.run_method(self.r)   
        return

    def post(self):
        self.run_method(self.c)
        return

    def put(self):
        self.run_method(self.u)
        return

    def delete(self):
        self.run_method(self.d)
        return

    def send_message(self, client_id, message):
        try:
            channel.send_message(client_id, simplejson.dumps(message))
        except:
            pass
        
    def error_data(self, err):
        return {
            'type' : 'error',
            'error' : err
        }

    def get_args(self):
        query_dict = {}

        query_string = self.request.query_string
        post_data = simplejson.loads(self.request.body)

        query_dict.update(urlparse.parse_qs(query_string))
        query_dict.update(post_data)
        
        return query_dict

    def run_method(self, method):
        try:
            kwargs = self.get_args()
            data = method(**kwargs)
        except Exception, err:
            data = self.error_data(err)

        self.write_json(data)
        
        return
            
    def write_json(self, data):
        self.response.out.write(simplejson.dumps({
            'data': data
        }))
        return
