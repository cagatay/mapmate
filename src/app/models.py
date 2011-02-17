from google.appengine.ext import db

from lib import geohash

class Box(db.Model):
    box_hash = db.StringProperty()
    ne = db.GeoPtProperty()
    sw = db.GeoPtProperty()

    def save(self):
        if not self.box_hash:
            self.box_hash = self.key().name()
            bounds = geohash.bbox(self.box_hash)
            self.ne = db.GeoPt(bounds['n'], bounds['e'])
            self.sw = db.GeoPt(bounds['s'], bounds['w'])
            self.put()
        return

class User(db.Model):
    fb_uid           = db.StringProperty()
    online           = db.BooleanProperty()
    location         = db.GeoPtProperty()
    last_update      = db.DateTimeProperty(auto_now = True)
    box              = db.ReferenceProperty(Box)

    def save(self, location):
        lat = location['lat']
        lng = location['lng']

        loc = db.GeoPt(lat, lng)
        loc_hash = geohash.encode(lat, lng)
        bbox_hash = loc_hash[:6]

        bbox = Box.get_or_insert(bbox_hash)
        bbox.save()

        self.location = loc
        self.online = True
        self.box = bbox
        self.fb_uid = self.key().name()
        self.put()

class Chat(db.Model):
    starter          = db.ReferenceProperty(User, collection_name = 'started_set')
    participant      = db.ReferenceProperty(User, collection_name = 'participated_set')
    date             = db.DateTimeProperty(auto_now_add = True)

class Message(db.Model):
    chat             = db.ReferenceProperty(Chat)
    sender           = db.ReferenceProperty(User, collection_name = "sent_set")
    text             = db.TextProperty()
    date             = db.DateTimeProperty(auto_now_add = True)
    read             = db.BooleanProperty(default = False)

class Shout(db.Model):
    box              = db.ReferenceProperty(Box)
    user             = db.ReferenceProperty(User)
    text             = db.StringProperty()
    date             = db.DateTimeProperty(auto_now_add = True)
