from controllers import index
from controllers import rpc

route = [
         ('/', index.controller),
         ('/channel', rpc.controller)
         ]