import logging

logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, name, username):
        self.name = name
        self.username = username

    def __str__(self):
        return "User(Name: '%s', Username: '%s')" % (self.name, self.username)
