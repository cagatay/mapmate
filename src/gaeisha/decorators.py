def require_auth(func):
    def inner_func(self, *args, **kwargs):
        if self.current_user():
            return func(self, *args, **kwargs)
        else:
            return { 
                'type' : 'authError' 
            }
    return inner_func
