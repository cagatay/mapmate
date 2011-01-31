from gaeisha.app import controller
from lib import facebook
import settings

from models import User

class baseController(controller):
    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user = facebook.get_user_from_cookie(self.request.cookies,
                                                    settings.FACEBOOK_API_KEY,
                                                    settings.FACEBOOK_APP_SECRET)
            if user:
                self._access_token = user['access_token']
                self._uid = user['uid']
                self._current_user = User.get_by_key_name(self._uid)
        return self._current_user
