from google.appengine.ext import db

'''
 model class
'''

class model(db.Model):
    
    @classmethod
    def fetch(cls, filter = dict(), limit = 1000):
        query = cls.all()
        
        for key, value in filter.iteritems():
            query.filter(key, value)
        
        return query.fetch(limit)
