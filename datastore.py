from google.appengine.ext import ndb

STATUS_NEW = 0
STATUS_PENDING = 1
STATUS_AUTH = 2


class User(ndb.Model):
    status = ndb.IntegerProperty(default=STATUS_NEW)
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    admin = ndb.BooleanProperty(default=False)


class Ping(ndb.Model):
    date = ndb.DateTimeProperty()