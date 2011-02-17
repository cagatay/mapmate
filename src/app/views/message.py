from app.views import base
from app.models import User, Chat, Message
from app.decorators import require_auth, json_in, json_out

class view(base.view):

    @json_out
    @require_auth
    def get(self):
        user = User.get_by_key_name(self.fb_uid)
        if not user:
            raise Exception('user is not initialized')

        return

    @json_in
    @json_out
    @require_auth
    def post(self, reciepent, text):
        reciepent = User.get_by_key_name(reciepent)
        sender = User.get_by_key_name(self.fb_uid)

        chat = Chat.get_or_insert(sender.fb_uid + '|' + reciepent.fb_uid,
                                  starter = sender,
                                  participant = reciepent)

        message = Message(chat = chat, sender = sender, text = text)
        message.put()

        chat.date = message.date
        chat.put()

        self.send_message(reciepent.fb_uid, {
            'type' : 'new-message',
            'message' : message,
        })

        return True 
