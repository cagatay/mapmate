from app.views import user, message, chat

urls = [
    ('/user*', user.view),
    ('/message*', message.view),
    ('/chat*', chat.view)
]
