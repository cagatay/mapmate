from app.views import base
from app.models import User
from app.decorators import require_auth, json_in, json_out

class view(base.view):

    @json_out
    @require_auth
    def get(self):
        user = User.get_by_key_name(self.fb_uid)
        if not user:
            raise Exception('user is not initialized')

