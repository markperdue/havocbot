import logging

logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, text, user, channel, event, timestamp):
        self.text = text
        self.user = user
        self.channel = channel
        self.event = event
        self.timestamp = timestamp

    def __str__(self):
        return "Message(Text: '%s', User: '%s', Channel: '%s', Type: '%s')" % (self.text, self.user, self.channel, self.event)
