# gae imports #
from google.appengine.ext.webapp import util
from google.appengine.ext import webapp

# gaeisha imports #
import settings
import route

def main():
    application = webapp.WSGIApplication(route.urls, settings.DEBUG)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
