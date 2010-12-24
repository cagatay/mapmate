'''
Created on Dec 22, 2010

@author: cagatay
'''
import logging
import yaml
import os.path

from google.appengine.api import channel
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template, util
from django.utils import simplejson

first_run     = True
config        = dict()
controllers   = list()

# TODO: exception handling

class model(db.Model):
    
    @classmethod
    def fetch(cls, filter = dict(), limit = 1000):
        query = cls.all()
        
        for key, value in filter.iteritems():
            query.filter(key, value)
        
        return query.fetch(limit)
    pass 

class Controller(webapp.RequestHandler):

    def get(self, templateDict=None):
        if self.run_before:
            self.run_before()
        if not self.template_dict:
            self.template_dict = dict()
        
        self.template_dict.update({ 'debug' : config['debug'] })
        self.writeTemplate(self.template_file, self.template_dict)
        
        return
    
    def post(self):
        args = simplejson.loads(self.request.body)
        
        func = args['function']
        del args['function']

        if func.startswith("rpc"):
            func = getattr(self, func)
            result = func(**args)
            self.writeJson(result)
        else:
            self.error(404)
        return
    
    def writeTemplate(self, templateFile, templateDict):
        templatePath = os.path.join(os.path.dirname(__file__), config['template_path'] + templateFile)
        self.response.out.write(template.render(templatePath, templateDict))
        
        return
    
    def sendMessage(self, client_id, message):
        try:
            channel.send_message(client_id, simplejson.dumps(message))
        except:
            pass
        
    def writeJson(self, data):
        self.response.out.write(simplejson.dumps(data))
        return
    

def load_config():
    global config
    
    try:
        config_file = file('gaeisha.yaml')
        file_content = config_file.read()
    except:
        raise Exception("can not open config file")
    else: 
        try:
            config = yaml.load(file_content)
        except:
            raise Exception("can not parse config file")
        finally:
            config_file.close()
    return

def load_controllers():
    global controllers
    global config
    
    try:
        controller_package = __import__(name = config["controller_package"])
        controllers = getattr(controller_package, 'route')
    except ImportError as e:
        raise e
    return
 
def init_application():
    global is_initialised
    global controllers 
    global config
    global first_run
    
    if first_run:
        try:
            load_config()
            load_controllers()
        except Exception as e:
            raise e
        else:
            first_run = False

def main():
    init_application()
    application = webapp.WSGIApplication(controllers, debug=config['debug'] )
    util.run_wsgi_app(application)
    
if __name__ == "__main__":
    main()