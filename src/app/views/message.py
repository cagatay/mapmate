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
        other = self.request.get('uid')

        chatjoin = ChatJoin.get_chat(user.fb_uid, other)
        chat = chatjoin.chat_set.filter('user = ', user).get()
        if chat:
            chat.read = True
            chat.put()
        return chatjoin.message_set.order('-date').fetch(10)

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

        chat = Chat(key_name = sender.fb_uid + '|' + reciepent.fb_uid,
                    chatjoin = chatjoin,
                    user = sender,
                    other = reciepent,
                    date = message.date,
                    last_message_text = message.text,
                    read = True)
        chat.put()

        chat = Chat(key_name = reciepent.fb_uid + '|' + sender.fb_uid,
                    chatjoin = chatjoin,
                    user = reciepent,
                    other = sender,
                    date = message.date,
                    last_message_text = message.text,
                    read = False)
        chat.put()

        self.send_message(reciepent.fb_uid, {
            'type' : 'new-chat',
            'chat' : chat,
        })
        return True

    @json_in
    @require_auth
    def put(self):
        return True 
