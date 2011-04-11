from google.appengine.ext import webapp
from google.appengine.api import channel
from lib import json

from lib import facebook
import settings
import traceback
import logging

class view(webapp.RequestHandler):
    def _get_fb_user(self):
        self.fb_uid = None
        user = facebook.get_user_from_cookie(self.request.cookies,
                                             settings.FACEBOOK_APP_ID,
                                             settings.FACEBOOK_APP_SECRET)
        if user:
            self.fb_access_token = user['access_token']
            self.fb_uid = user['uid']

    def initialize(self, request, response):
        webapp.RequestHandler.initialize(self, request, response)
        self._get_fb_user()

    def create_channel(self):
        return channel.create_channel(self.fb_uid)

    def send_message(self, client_id, message):
        try:
            channel.send_message(client_id, json.encode(message))
        except:
            traceback.print_exc()

    def error_data(self, err):
        return {
            'type' : 'error',
            'error' : str(err)
        }


    def write_json(self, data):
        self.response.out.write(json.encode({
            'data': data
        }))
        return
