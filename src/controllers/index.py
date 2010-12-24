'''
Created on Dec 22, 2010

@author: cagatay
'''

from gaeisha import Controller, config
from google.appengine.api import users, channel

class controller(Controller):
    template_file = 'index.html'
    template_dict = dict()
    
    def run_before(self):
        googleUser = users.get_current_user()
            
        if googleUser:
            authlink = users.create_logout_url('/')
            authtext = 'logout'
            auth = True
            channelKey = googleUser.user_id()
            self.template_dict.update({'channelKey' : channelKey,
                                       'token'      : channel.create_channel(channelKey)
                                      })
            if config['debug']:
                lat = self.request.get('lat')
                lng = self.request.get('lng')
                if not (lat and lng):
                    lat = '40.968242'
                    lng = '28.8228'
                self.template_dict.update({ 'lat' : lat,
                                            'lng' : lng})
            
        else:
            authlink = users.create_login_url('/')
            authtext = 'login'
            auth = False
        
        self.template_dict.update({'authlink' : authlink,
                                   'authtext' : authtext,
                                   'auth'     : auth
                                  })
        
def main():
    pass
if __name__ == '__main__':
    main()