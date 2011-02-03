from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.api import channel

from lib import json
import logging

'''
 Handler class
'''

class handler(webapp.RequestHandler):

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
            'error' : str(err)
        }

    @property
    def query(self):
        if not hasattr(self, '_query'):
            self._query = {}
            parts = self.request.query_string.split('&')

            for p in parts:
                try:
                    key, value = p.split('=')
                    self._query[key] = value
                except:
                    pass

            post_data = self.request.body
            if post_data:
                post_data = simplejson.loads(post_data)
                
                # workaround for python issue2646
                for key, value in post_data.iteritems():
                    self._query[key.encode('utf-8')] = value
        return self._query
            

    def run_method(self, method):
        try:
            logging.debug(self.query)
            data = method(**self.query)
        except Exception, err:
            data = self.error_data(err)

        self.write_json(data)
        
        return
            
    def write_json(self, data):
        self.response.out.write(json.encode({
            'data': data
        }))
        return
