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
    fb_uid = db.StringProperty()
    online = db.BooleanProperty()
    location = db.GeoPtProperty()
    last_update = db.DateTimeProperty(auto_now = True)
    box = db.ReferenceProperty(Box)

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

class ChatJoin(db.Model):
    @classmethod
    def get_chat(cls, sender, reciepent):
        # to make a unique key out of sender-reciepent uids
        if sender < reciepent:
            sender, reciepent = reciepent, sender
        chat_key = sender + '|' + reciepent
        
        return cls.get_or_insert(chat_key)

class Message(db.Model):
    chatjoin = db.ReferenceProperty(ChatJoin)
    sender = db.ReferenceProperty(User, collection_name = 'sent_set')
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add = True)

class Chat(db.Model):
    chatjoin = db.ReferenceProperty(ChatJoin)
    date = db.DateTimeProperty(auto_now_add = True)
    user = db.ReferenceProperty(User)
    other = db.ReferenceProperty(User, collection_name='other_set')
    last_message_text = db.TextProperty()
    read = db.BooleanProperty(default = False)

class Shout(db.Model):
    box = db.ReferenceProperty(Box)
    user = db.ReferenceProperty(User)
    text = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add = True)
