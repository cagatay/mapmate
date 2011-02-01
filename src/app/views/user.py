'''
Created on Dec 25, 2010

@author: cagatay
'''

from lib import geohash

from gaeisha.base import handler
from google.appengine.api import channel, urlfetch
from gaeisha.decorators import require_auth

from gaeisha.plugins import gaeisha_fb

from app.models import User

class view(handler):
    
    @require_auth
    def r(self, user_id=None):
        response = None

        if user_id:
            user = User.get_by_key_name(user_id)
            response = user
        else:
            current_user = User.get_by_key_name(self.current_user())
            if not current_user:
                raise Exception('user is not initialized')

            bbox_hash = current_user.bbox_hash
            users = User.fetch({ 'bbox_hash =': bbox_hash })
            
            response = users
            
        return response

'''
########################## rpcSendMessage ################################    
    @require_auth
    def rpc_send_message(self, args):
        recipient = args['recipient']
        text = args['text']
        response = list()
        sender = self.current_user
        receiver = User.get_by_key_name(recipient)
        
        
        message = Message()
        message.sender = sender
        message.receiver = receiver
        message.text = text
        message.put()
        
        self.sendMessage(recipient, [{ 'type' : 'receivedMessage',
                                      'data' : {
                                                  'from'      : sender.name,
                                                  'date'      : str(message.date),
                                                  'isRead'    : False,
                                                  'text'      : text,
                                                  'senderKey' : sender.id,
                                                  'messageKey': message.key().id()
                                                  }
                                    }])
    
        response.append({
                             'type'    : 'sentMessage',
                             'data'    : {
                                          'to'          : receiver.name,
                                          'date'        : str(message.date),
                                          'text'        : message.text,
                                          'receiverKey' : receiver.id,
                                          'messageKey'  : message.key().id()
                                          }
                             })        
        return response
#############################################################################

    
######################## rpcGetSentMessages #################################
    def rpcGetSentMessages(self, args=None):
        response = list()
        user = self.current_user
        
        if user:
            sentMessages = Message.fetch({
                                          'sender ='        : user,
                                          'senderDeleted =' : False
                                          })
            for message in sentMessages:
                response.append({
                                 'type'    : 'sentMessage',
                                 'data'    : {
                                              'to'          : message.receiver.name,
                                              'date'        : str(message.date),
                                              'text'        : message.text,
                                              'receiverKey' : message.receiver.id,
                                              'messageKey'  : message.key().id()
                                              }
                                 })
        else:
            response.append( { 'type' : 'error' })
        
        return response
#############################################################################


######################## rpcGetReceivedMessages #############################
    def rpcGetReceivedMessages(self):
        response = list()
        
        user = self.current_user
        if user:
            receivedMessages = Message.fetch({
                                              'receiver ='        : user,
                                              'receiverDeleted =' : False
                                            })
            for message in receivedMessages:
                response.append({ 'type' : 'receivedMessage',
                                  'data' : {
                                              'from'      : message.sender.name,
                                              'date'      : str(message.date),
                                              'isRead'    : message.isRead,
                                              'text'      : message.text,
                                              'senderKey' : message.sender.id,
                                              'messageKey': message.key().id()
                                              }
                                 })
        else:
            response.append({'type' : 'error'})
        
        return response
#############################################################################


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
################################################################################################

    @require_auth
    def rpc_get_token(self, data=None):
        user = self.current_user
        token         = channel.create_channel(user.id)
        response = {
            'data' : {
                'token' : token
            }
        }
        return response


########################### rpcInit ############################################################ 
    @require_auth
    def rpc_init(self, args):
        location = args['location']
        response = list()
        
        user = self.current_user
        locationHash  = geohash.encode(location['lat'], location['lng'])
        outerBoxHash  =  locationHash[:6]
        bbox = geohash.bbox(outerBoxHash)
        adjacentBoxes = geohash.expand(locationHash)
            
        user.isOnline         = True
        user.location         = db.GeoPt(location['lat'], location['lng'])
        user.locationHash     = locationHash
        user.outerBoxHash     = outerBoxHash
        user.adjacentBoxes    = adjacentBoxes
        user.put()
            
        usersAround = self.rpcUsersAround(outerBoxHash)
        response.extend(usersAround)
        
        receivedMessages = self.rpcGetReceivedMessages()
        response.extend(receivedMessages)
        
        sentMessages = self.rpcGetSentMessages()
        response.extend(sentMessages)

        response.extend({'bbox' : bbox})
            
        return response
######################################################################################################


##################### rpcClose ####################################################################### 
    @require_auth
    def rpcClose(self, args=None):
        user = self.current_user
        if user:
            user.isOnline = False
            for other in user.inScope:
                self.sendMessage(other, [{
                                            'type' : 'removeUser',
                                            'data' : { 
                                                      "key"        : user.id 
                                                      }
                                            }])
                user.inScope = list()
            user.put()
        return None

class oauthController(baseController):
    def get(self):
        verification_code = self.request.get("code")
        
        if self.current_user:
            self.redirect('/')
            
        elif verification_code:
            access_token = self.get_access_token(verification_code)
            
            graph = facebook.GraphAPI(access_token)
            profile = graph.request(path = 'me', args = dict(fields ='id,name,first_name,picture,link'))
            
            user = User(key_name          = str(profile['id']),
                        firstName         = profile['first_name'],
                        picture           = db.Blob(urlfetch.Fetch(profile['picture']).content),
                        id                = str(profile['id']),
                        name              = profile['name'],
                        accessToken       = access_token, 
                        profileUrl        = db.Link(profile['link']))
            user.put()
            
            self.set_cookie("fb_user", str(profile["id"]))
            self.redirect("/")
        else:
            self.redirect_auth()
        return

if __name__ == "__main__":
    main()
'''
