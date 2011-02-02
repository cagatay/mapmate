def require_init(func):
    def inner_func(self, *args, **kwargs):
        if self.current_user():
            return func(self, *args, **kwargs)
        else:
            raise Exception('you need to be signed in')
    return inner_func
