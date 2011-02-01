'''
Created on Dec 25, 2010

@author: cagatay
'''

from lib import geohash

from gaeisha.base import handler
from google.appengine.api import channel
from google.appengine.ext import db
from gaeisha.decorators import require_auth

from gaeisha.plugins import gaeisha_fb

from app.models import User

class view(handler):
    
    def c(self):
        pass

    @require_auth
    def r(self, user_id=None):
        response = None

        if user_id:
            user = User.get_by_key_name(user_id)

            if user:
                response = user
            else:
                raise Exception('no such user')
        else:
            current_user = User.get_by_key_name(self._uid)
            if not current_user:
                raise Exception('user is not initialized')

            bbox_hash = current_user.bbox_hash
            users = User.fetch({ 'bbox_hash =': bbox_hash })
            
            response = users

        return response

    @require_auth
    def u(self, location):
        uid = self._uid
        token = channel.create_channel(uid)
        location_hash = geohash.encode(location['lat'], location['lng'])
        bbox_hash = location_hash[:8]
        bbox = geohash.bbox(bbox_hash)

        user = User(key_name = uid,
                    location = db.GeoPt(location['lat'], location['lng']),
                    location_hash = location_hash,
                    bbox_hash = bbox_hash)
        user.put()

        return {
            'token' : token,
            'bbox'  : bbox
        }

    @require_auth
    def d(self):
        uid = self._uid
        
        user = User.get_by_key_name(uid)
        user.online = False

        for x in user.scope:
            self.sendMessage(x, [{
                'type' : 'removeUser',
                'data' : { 
                     "key"  : uid
                 }
            }])

        user.scope = list()
        user.put()

        return

'''

######################## rpcUsersAround ######################################    
    def rpcUsersAround(self, args):
        if 'bounds' in args:
            bounds = args['bounds']
        else:
            bounds = args
        # TODO: Exception handling
        response = list()
        
        thisUser = self.current_user
        if thisUser:
            inScopeList = list()
            usersAround = User.fetch({
                                      'isOnline ='     : True,
                                      'id      !='     : thisUser.id,
                                      'outerBoxHash =' : thisUser.outerBoxHash
                                      })
            filter(lambda x: x.location.lat < bounds['north_east']['lat']
                         and x.location.lat > bounds['south_west']['lat']
                         and x.location.lon < bounds['north_east']['lng']
                         and x.location.lon > bounds['south_west']['lng'], usersAround)
            for user in usersAround:
                response.append({ 
                                 "type"        : 'addUser',
                                 'data'        : {
                                                   "key"         : user.id,
                                                   "name"        : user.firstName,
                                                   "location"    : {
                                                                    'lat' : user.location.lat,
                                                                    'lng' : user.location.lon
                                                                    }
                                                   }
                                 })
                
                self.sendMessage(user.id, [{
                                                           'type' : 'addUser',
                                                           'data' : { 
                                                                     "key"        : thisUser.id,
                                                                     "name"       : thisUser.firstName,
                                                                     "location"   : {
                                                                                     'lat' : thisUser.location.lat,
                                                                                     'lng' : thisUser.location.lon
                                                                                     } 
                                                                     }
                                                           }])
                inScopeList.append(user.id)
                
            thisUser.inScope = inScopeList
            thisUser.put() 
        else:
            response.append( { 'type' : 'error' }) 
            
        return response
'''

if __name__ == "__main__":
    main()
