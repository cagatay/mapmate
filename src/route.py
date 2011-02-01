from app.views import user, message

urls = [
    ('/user*', user.view),
    ('/message*', message.view)
]
