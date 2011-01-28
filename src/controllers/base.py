import base64
import Cookie
import email.utils
import time
import logging
import hmac
import hashlib

from lib import facebook
from gaeisha.app import controller
import settings

from models import User

class baseController(controller):
    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected."""
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = self.parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = User.get_by_key_name(user_id)
        return self._current_user

    def redirect_auth(self):
        args = dict(redirect_uri=self.request.path_url)
        args['client_id'] = settings.FACEBOOK_CLIENT_ID
        args['display'] = 'touch'
        self.redirect(settings.FACEBOOK_AUTH_URL)
        
    def set_cookie(self, name, value, domain=None, path="/", expires=None):
        """Generates and signs a cookie for the give name/value"""
        timestamp = str(int(time.time()))
        value = base64.b64encode(value)
        signature = self.cookie_signature(value, timestamp)
        cookie = Cookie.BaseCookie()
        cookie[name] = "|".join([value, timestamp, signature])
        cookie[name]["path"] = path
        if domain: cookie[name]["domain"] = domain
        if expires:
            cookie[name]["expires"] = email.utils.formatdate(
                expires, localtime=False, usegmt=True)
        self.response.headers._headers.append(("Set-Cookie", cookie.output()[12:]))
    
    def parse_cookie(self, value):
        """Parses and verifies a cookie value from set_cookie"""
        if not value: return None
        parts = value.split("|")
        if len(parts) != 3: return None
        if self.cookie_signature(parts[0], parts[1]) != parts[2]:
            logging.warning("Invalid cookie signature %r", value)
            return None
        timestamp = int(parts[1])
        if timestamp < time.time() - 30 * 86400:
            logging.warning("Expired cookie %r", value)
            return None
        try:
            return base64.b64decode(parts[0]).strip()
        except:
            return None
    
    
    def cookie_signature(self, *parts):
        """Generates a cookie signature.
    
    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
        hash = hmac.new(settings.FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
        for part in parts: hash.update(part)
        return hash.hexdigest()
    
    def get_access_token(self, code):
        return facebook.get_access_token(settings.FACEBOOK_APP_SECRET,
                code, self.request.path_url, settings.FACEBOOK_CLIENT_ID)
