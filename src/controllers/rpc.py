'''
Created on Dec 22, 2010

@author: cagatay
'''

from gaeisha import Controller
from google.appengine.api import users
from google.appengine.ext import db
from models import User
from models import Message
from lib import geohash

class controller(Controller):

########################## rpcUpdateState ###############################
    def rpcUpdateState(self, state):
        # TODO: implement
        return
#########################################################################


########################## rpcSendMessage ################################    
    def rpcSendMessage(self, recipient, text):
        response = list()
        sender = users.get_current_user()
        if sender:
            senderData = User.get_by_key_name(sender.user_id())
            
            receiver = User.get_by_key_name(recipient)
            
            
            message = Message()
            message.sender = senderData
            message.receiver = receiver
            message.text = text
            message.put()
            
            self.sendMessage(recipient, { 'type' : 'receivedMessage',
                                          'data' : {
                                                      'from'      : sender.nickname(),
                                                      'date'      : message.date,
                                                      'isRead'    : False,
                                                      'text'      : text,
                                                      'senderKey' : sender.user_id(),
                                                      'messageKey': message.key().id()
                                                      }
                                        })
        
            response.append({ 'type' : 'ok' })
        else:
            response.append({ 'type' : 'error'})
        
        return response
#############################################################################

    
######################## rpcGetSentMessages #################################
    def rpcGetSentMessages(self):
        response = list()
        googleUser = users.get_current_user()
        
        if googleUser:
            sentMessages = Message.fetch({
                                          'sender ='        : googleUser,
                                          'senderDeleted =' : False
                                          })
            for message in sentMessages:
                response.append({
                                 'type'    : 'sentMessage',
                                 'data'    : {
                                              'to'          : message.receiver.authUser.nickname(),
                                              'date'        : message.date,
                                              'text'        : message.text,
                                              'receiverKey' : message.receiver.authUser.user_id(),
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
        googleUser = users.get_current_user()
        if googleUser:
            receivedMessages = Message.fetch({
                                              'receiver ='        : googleUser,
                                              'receiverDeleted =' : False
                                            })
            for message in receivedMessages:
                response.append({ 'type' : 'receivedMessage',
                                  'data' : {
                                              'from'      : message.sender.authUser.nickname(),
                                              'date'      : message.date,
                                              'isRead'    : message.isRead,
                                              'text'      : message.text,
                                              'senderKey' : message.sender.authUser.user_id(),
                                              'messageKey': message.key().id()
                                              }
                                 })
        else:
            response.append({'type' : 'error'})
        
        return response
#############################################################################


######################## rpcUsersAround ######################################    
    def rpcUsersAround(self, bounds):
        # TODO: Exception handling
        response = list()
        
        googleUser = users.get_current_user()
        if googleUser:
            thisUser = User.get_by_key_name(googleUser.user_id())
            usersAround = User.fetch({
                                      'isOnline ='     : True,
                                      'authUser !='    : googleUser,
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
                                                   "key"         : user.authUser.user_id(),
                                                   "name"        : user.authUser.nickname(),
                                                   "location"    : {
                                                                    'lat' : user.location.lat,
                                                                    'lng' : user.location.lon
                                                                    }
                                                   }
                                 })
                
                self.sendMessage(user.authUser.user_id(), {
                                                           'type' : 'add_user',
                                                           'data' : { 
                                                                     "key"        : googleUser.user_id(),
                                                                     "name"       : googleUser.nickname(),
                                                                     "location"   : {
                                                                                     'lat' : thisUser.location.lat,
                                                                                     'lng' : thisUser.location.lon
                                                                                     } 
                                                                     }
                                                           }) 
        else:
            response.append( { 'type' : 'error' }) 
            
        return response
################################################################################################


########################### rpcInit ############################################################ 
    def rpcInit(self, location, bounds):
        response = list()
        
        googleUser = users.get_current_user()
        if googleUser:
            user = User.get_by_key_name(googleUser.user_id())
            
            locationHash  = geohash.encode(location['lat'], location['lng'])
            outerBoxHash  = locationHash[:6]
            adjacentBoxes = geohash.expand(locationHash)
            
            if (user):
                user.isOnline         = True
                user.location.lat     = location['lat']
                user.location.lon     = location['lng']
                user.locationHash     = locationHash
                user.outerBoxHash     = outerBoxHash
                user.adjacentBoxes    = adjacentBoxes
                user.put()
            else:
                # first time
                user = User(key_name          = googleUser.user_id(), 
                            isOnline          = True,
                            authUser          = googleUser, 
                            location          = db.GeoPt(location['lat'], location['lng']),
                            locationHash      = locationHash,
                            outerBoxHash      = outerBoxHash,
                            adjacentBoxes     = adjacentBoxes)
                user.put()
            
            
            usersAround = self.rpcUsersAround(bounds)
            response.extend(usersAround)
            
            receivedMessages = self.rpcGetReceivedMessages()
            response.extend(receivedMessages)
            
            sentMessages = self.rpcGetSentMessages()
            response.extend(sentMessages)
        else:
            response.append({'type' : 'error'})
            
        return response
######################################################################################################


##################### rpcClose ####################################################################### 
    def rpcClose(self):
        googleUser = users.get_current_user()
        if googleUser:
            user = User.get_by_key_name(googleUser.user_id())
            user.isOnline = False
            user.put()
######################################################################################################

def main():
    pass
if __name__ == '__main__':
    main()