from havocbot.stashertinydb import StasherTinyDB
from havocbot.stasher import StasherDB


class StasherFactory(object):
    def factory(factory_type):
        if factory_type == "StasherTinyDB":
            return StasherTinyDB()
        elif factory_type == "StasherDB":
            return StasherDB()
        else:
            return StasherTinyDB()
    factory = staticmethod(factory)
