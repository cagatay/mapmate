'''
Created on Dec 25, 2010

@author: cagatay
'''

from app.models import User
from app.views import base
from app.decorators import require_auth, json_in, json_out

class view(base.view):
    
    @json_out
    @require_auth
    def get(self):
        user = User.get_by_key_name(self.fb_uid)
        if not user:
            raise Exception('user is not initialized')

        query = user.box.user_set
        query.filter('online =', True)
        scope = []

        for x in query:
            self.send_message(x.fb_uid, {
                'type' : 'add-mate',
                'mate' : user
            })
            scope.append(x)
        return scope

    @json_in
    @json_out
    @require_auth
    def post(self, location):
        user = User.get_or_insert(self.fb_uid)
        user.save(location)

        user.token = self.create_channel()

        return user

    @require_auth
    def delete(self):
        uid = self.fb_uid
        
        user = User.get_by_key_name(uid)
        user.online = False
        user.put()

        scope = user.box.user_set.filter('online =', True)

        for x in scope:
            self.send_message(x.fb_uid, {
                'type' : 'remove-mate',
                'uid'  : uid
            })

        return

def main():
    return

if __name__ == "__main__":
    main()
