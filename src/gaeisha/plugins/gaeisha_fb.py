from gaeisha.base import handler
from lib import facebook
import settings

def current_user(self):
    if not hasattr(self, "_current_user"):
        self._current_user = None
        user = facebook.get_user_from_cookie(self.request.cookies,
                                             settings.FACEBOOK_API_KEY,
                                             settings.FACEBOOK_APP_SECRET)
        if user:
            self._access_token = user['access_token']
            self._uid = user['uid']
    return self._current_user

handler.current_user = current_user
