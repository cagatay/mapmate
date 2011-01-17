'''
Created on Dec 25, 2010

@author: cagatay
'''

import logging
import yaml
import os
import base64
import Cookie
import email.utils
import time
import hashlib
import hmac
import urllib
import facebook
import geohash

from google.appengine.api import channel, urlfetch
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template, util
from django.utils import simplejson

first_run     = True
config        = dict()


# TODO: exception handling

'''
 model class
'''
class model(db.Model):
    
    @classmethod
    def fetch(cls, filter = dict(), limit = 1000):
        query = cls.all()
        
        for key, value in filter.iteritems():
            query.filter(key, value)
        
        return query.fetch(limit)
    pass 


'''
 Controller class
'''
class Controller(webapp.RequestHandler):

    def get(self, templateDict=None):
        if not self.template_dict:
            self.template_dict = dict()
        
        self.template_dict.update({ 'debug' : config['debug'] })
        self.writeTemplate(self.template_file, self.template_dict)
        
        return
    
    def post(self):
        args = simplejson.loads(self.request.body)
        
        func = args['func']
        del args['func']

        if func.startswith("rpc"):
            func = getattr(self, func)
            result = func(args)
            if result:
                self.writeJson({
                    'data' : result
                })
        else:
            self.error(404)
        return
    
    def writeTemplate(self, templateFile, templateDict):
        templatePath = os.path.join(os.path.dirname(__file__), config['template_path'] + templateFile)
        self.response.out.write(template.render(templatePath, templateDict))
        
        return
    
    def sendMessage(self, client_id, message):
        try:
            channel.send_message(client_id, simplejson.dumps(message))
        except:
            pass
        
    def writeJson(self, data):
        self.response.out.write(simplejson.dumps(data))
        return

class User(model):
    id              = db.StringProperty()
    name            = db.StringProperty()
    firstName       = db.StringProperty()
    picture         = db.BlobProperty()
    accessToken     = db.StringProperty()
    profileUrl      = db.LinkProperty()
    isOnline        = db.BooleanProperty()
    location        = db.GeoPtProperty()
    lastUpdate      = db.DateTimeProperty(auto_now = True)
    locationHash    = db.StringProperty()
    outerBoxHash    = db.StringProperty()
    adjacentBoxes   = db.StringListProperty(),
    inScope         = db.StringListProperty()

class Message(model):
    sender          = db.ReferenceProperty(User, collection_name = "sender")
    receiver        = db.ReferenceProperty(User, collection_name = "receiver")
    text            = db.TextProperty()
    date            = db.DateTimeProperty(auto_now_add = True)
    isRead          = db.BooleanProperty(default = False)
    senderDeleted   = db.BooleanProperty(default = False)
    receiverDeleted = db.BooleanProperty(default = False)

class baseController(Controller):
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
        args.update(get_config('facebook_param'))
        self.redirect(get_config('facebook_auth_url') + urllib.urlencode(args))
        
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
        hash = hmac.new(get_config('facebook_app_secret'), digestmod=hashlib.sha1)
        for part in parts: hash.update(part)
        return hash.hexdigest()
    
    def get_access_token(self, code):
        return facebook.get_access_token(get_config('facebook_app_secret'), code, self.request.path_url, get_config('facebook_param')['client_id'])
    
''' cagatay '''
def require_auth(func):
    def inner_func(self, *args, **kwargs):
        if self.current_user:
            return func(self, *args, **kwargs)
        else:
            return { 
                'type' : 'authError' 
            }
    return inner_func

class indexController(baseController):
    template_file = 'index-new.html'

##############################################################################
# rpcController class
##############################################################################
class rpcController(baseController):

########################## rpcUpdateState ###############################
    def rpcUpdateState(self, args):
        # TODO: implement
        return
#########################################################################


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
            '''
            filter(lambda x: x.location.lat < bounds['north_east']['lat']
                         and x.location.lat > bounds['south_west']['lat']
                         and x.location.lon < bounds['north_east']['lng']
                         and x.location.lon > bounds['south_west']['lng'], usersAround)
            '''
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

class picController(baseController):
    def get(self):
        if self.current_user:
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
        else:
            self.error(403)


'''
  module functions
'''
def load_config():
    global config
    
    try:
        config_file = file('gaeisha.yaml')
        file_content = config_file.read()
    except:
        raise Exception("can not open config file")
    else: 
        try:
            config = yaml.load(file_content)
        except:
            raise Exception("can not parse config file")
        finally:
            config_file.close()
    return

def get_config(key):
    global config
    return config[key]

 
def init_application():
    global is_initialised
    global controllers 
    global config
    global first_run
    
    if first_run:
        load_config()
        first_run = False

routes = [
             ('/', indexController),
             ('/channel', rpcController),
             ('/oauth', oauthController),
             ('/pic', picController)
         ]

def main():
    init_application()
    application = webapp.WSGIApplication(routes, debug=config['debug'] )
    util.run_wsgi_app(application)
    
if __name__ == "__main__":
    main()
