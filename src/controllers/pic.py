from gaeisha import app
from gaiesha.decorators import require_auth

from models import User

class controller(app.controller):

    @require_auth
    def get(self):
        id = self.request.get('id')
        if id:
            user = User.get_by_key_name(id)
            if user:
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(user.picture)
            else:
                self.error(404)
        else:
            self.error(400)
