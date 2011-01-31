from gaeisha.db import model
from gaeisha.app import Controller
from gaeisha.plugins import gaeisha_fb
from google.appenginee.ext import db

class User(model):
    name             = db.StringProperty()
    first_name       = db.StringProperty()
    access_token     = db.StringProperty()
    profile_url      = db.LinkProperty()
    online           = db.BooleanProperty()
    location         = db.GeoPtProperty()
    last_update      = db.DateTimeProperty(auto_now = True)
    location_hash    = db.StringProperty()
    outer_hash       = db.StringProperty()
    adjacent_boxes   = db.StringListProperty()
    scope            = db.StringListProperty()

class Message(model):
    sender           = db.ReferenceProperty(User, collection_name = "sender")
    receiver         = db.ReferenceProperty(User, collection_name = "receiver")
    text             = db.TextProperty()
    date             = db.DateTimeProperty(auto_now_add = True)
    read             = db.BooleanProperty(default = False)
    sender_deleted   = db.BooleanProperty(default = False)
    receiver_deleted = db.BooleanProperty(default = False)

