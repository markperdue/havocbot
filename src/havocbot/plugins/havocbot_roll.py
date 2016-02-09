#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RollPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "a dice roller"

    @property
    def plugin_short_name(self):
        return "roll"

    @property
    def plugin_usages(self):
        return (
            ("!roll", None, "roll a 100 side dice "),
            ("!highroll", None, "roll a much larger dice"),
        )

    @property
    def plugin_triggers(self):
        return (
            ("!roll", self.start),
            ("!highroll", self.high_roll),
        )

    def init(self, havocbot):
        self.havocbot = havocbot

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.user)

        if message.channel and user:
            text = "%s rolled a %s" % (user.name, random.randrange(1, 101))
            callback.send_message(channel=message.channel, message=text)

    def high_roll(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.user)

        if message.channel and user:
            text = "%s rolled a %s" % (user.name, random.randrange(1, 10001))
            callback.send_message(channel=message.channel, message=text)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
