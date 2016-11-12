from havocbot.stashertinydb import StasherTinyDB
from havocbot.stasher import StasherDB


class StasherFactory(object):
    def factory(type):
        if type == "StasherTinyDB":
            return StasherTinyDB()
        elif type == "StasherDB":
            return StasherDB()
        else:
            return StasherTinyDB()
    factory = staticmethod(factory)