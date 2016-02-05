#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RollPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            "!roll": self.start,
            "!highroll": self.high_roll
        }
        self.help = {
            "description": "a dice roller",
            "usage": (
                ("!roll", None, "roll a 100 side dice "),
                ("!highroll", None, "roll a much larger dice"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        logger.info("start - message is '%s'" % (message))

        user = callback.get_user_by_id(message.user)
        # user = message.get_full_user_of_message()

        if message.channel and user:
            text = "%s rolled a %s" % (user.name, random.randrange(1, 101))
            callback.send_message(channel=message.channel, message=text)

    def high_roll(self, callback, message, **kwargs):
        logger.log(0, "high_roll - message is '%s'" % (message))

        user = callback.get_user_by_id(message.user)
        # user = message.get_full_user_of_message()

        if message.channel and user:
            text = "%s rolled a %s" % (user.name, random.randrange(1, 10001))
            callback.send_message(channel=message.channel, message=text)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
