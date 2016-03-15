class Message(object):
    def __init__(self, text, sender, to, event, timestamp):
        self.text = text
        self.sender = sender
        self.to = to
        self.event = event
        self.timestamp = timestamp

    def __str__(self):
        return "Message(Text: '%s', Sender: '%s', To: '%s', Type: '%s')" % (self.text, self.sender, self.to, self.event)
