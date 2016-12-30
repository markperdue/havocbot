class Message(object):
    def __init__(self, text, sender, to, event, client, timestamp):
        self.text = str(text)
        self.sender = str(sender)
        self.to = str(to)
        self.event = str(event)
        self.client = str(client)
        self.timestamp = timestamp

    def __str__(self):
        return "Message(Text: '%s', Sender: '%s', To: '%s', Event: '%s', Client: '%s', Timestamp: '%s')" \
               % (self.text, self.sender, self.to, self.event, self.client, self.timestamp)

    def reply(self):
        if self.event == 'groupchat':
            return self.to
        else:
            return self.sender


class FormattedThumbnailMessage(object):
    def __init__(self, text, default_text, thumbnail_url, attributes):
        self.text = text
        self.default_text = default_text
        self.thumbnail_url = thumbnail_url
        self.attributes = attributes


class FormattedMessage(object):
    def __init__(self, text, default_text, attributes):
        self.text = text
        self.default_text = default_text
        self.attributes = attributes
