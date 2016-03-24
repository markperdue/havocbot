class Message(object):
    def __init__(self, text, sender, to, event, client, timestamp):
        self.text = str(text)
        self.sender = str(sender)
        self.to = str(to)
        self.event = str(event)
        self.client = str(client)
        self.timestamp = timestamp

    def __str__(self):
        return "Message(Text: '%s', Sender: '%s', To: '%s', Type: '%s')" % (self.text, self.sender, self.to, self.event)
