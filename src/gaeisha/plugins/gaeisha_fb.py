from google.appengine.ext import webapp
from gaeisha.base import handler
from lib import facebook
import settings

def current_user(self):
    if not hasattr(self, "_current_user"):
        self._uid = None
        user = facebook.get_user_from_cookie(self.request.cookies,
                                             settings.FACEBOOK_CLIENT_ID,
                                             settings.FACEBOOK_APP_SECRET)
        if user:
            self._access_token = user['access_token']
            self._uid = user['uid']
    return self._uid

def initialize(self, request, response):
    webapp.RequestHandler.initialize(self, request, response)
    self.current_user()

handler.current_user = current_user
handler.initialize = initialize
