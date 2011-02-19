from app.views import base
from app.models import User, Chat, Message, ChatJoin
from app.decorators import require_auth, json_in, json_out

class view(base.view):

    @json_out
    @require_auth
    def get(self):
        user = User.get_by_key_name(self.fb_uid)
        if not user:
            raise Exception('user is not initialized')

        return user.chat_set.order('-date').fetch(10)

    @json_in
    @json_out
    @require_auth
    def post(self, reciepent, text):
        reciepent = User.get_by_key_name(reciepent)
        sender = User.get_by_key_name(self.fb_uid)

        chatjoin = ChatJoin.get_chat(sender.fb_uid, reciepent.fb_uid)

        message = Message(chatjoin = chatjoin, sender = sender, text = text)
        message.put()

        chatjoin.put()

        chats = chatjoin.chat_set.fetch(2)
        if not chats:
            chat_1 = Chat(chatjoin = chatjoin,
                          user = sender,
                          other = reciepent,
                          date = message.date,
                          last_message_text = message.text)
            chat_1.put()

            chat_2 = Chat(chatjoin = chatjoin,
                          user = reciepent,
                          other = sender,
                          date = message.date,
                          last_message_text = message.text)
            chat_2.put()

        self.send_message(reciepent.fb_uid, {
            'type' : 'new-message',
            'message' : message,
        })

        return True 
