class Room(object):
    def __init__(self, _id, name):
        self._id = str(_id)
        self.name = str(name)

    def __str__(self):
        return "Room(ID: '%s', Name: '%s')" % (self._id, self.name)
