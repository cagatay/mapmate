import traceback
from django.utils import simplejson

def require_auth(func):
    def inner_func(self, *args, **kwargs):
        if self.fb_uid:
            return func(self, *args, **kwargs)
        else:
            raise Exception('you need to be signed in')
    return inner_func

def json_out(func):
    def inner_func(self, *args, **kwargs):
        try:
            res = func(self, *args, **kwargs)
        except Exception, err:
            res = self.error_data(err)
            traceback.print_exc()

        self.write_json(res)
        return
    return inner_func

def json_in(func):
    def inner_func(self):
        data = self.request.body
        dict_ = {}
        kwargs = {}
        if data:
            try:
                dict_.update(simplejson.loads(data))
                # workaround for a bug in python2.5
                for key, val in dict_.iteritems():
                    kwargs[key.encode('utf-8')] = val
            except Exception:
                traceback.print_exc()
        func(self, **kwargs)
        return
    return inner_func
