from google.appengine.ext import db
from gaeisha import model

class User(model):
    authUser    	= db.UserProperty()
    isOnline    	= db.BooleanProperty()
    location		= db.GeoPtProperty()
    lastUpdate		= db.DateTimeProperty(auto_now = True)
    locationHash	= db.StringProperty()
    outerBoxHash	= db.StringProperty()
    adjacentBoxes	= db.StringListProperty()

class Message(model):
    sender          = db.ReferenceProperty(User, collection_name = "sender")
    receiver        = db.ReferenceProperty(User, collection_name = "receiver")
    text            = db.TextProperty()
    date            = db.DateTimeProperty(auto_now_add = True)
    isRead          = db.BooleanProperty(default = False)
    senderDeleted   = db.BooleanProperty(default = False)
    receiverDeleted = db.BooleanProperty(default = False)
