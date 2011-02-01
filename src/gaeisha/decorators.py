def require_auth(func):
    def inner_func(self, *args, **kwargs):
        if self._uid:
            return func(self, *args, **kwargs)
        else:
            raise Exception('you need to be signed in')
    return inner_func
