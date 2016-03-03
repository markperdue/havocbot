#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging
import random

logger = logging.getLogger(__name__)


class RollPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "a dice roller"

    @property
    def plugin_short_name(self):
        return "roll"

    @property
    def plugin_usages(self):
        return [
            ("!roll", None, "roll a 100 side dice "),
            ("!highroll", None, "roll a much larger dice"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!roll", self.start),
            ("!highroll", self.high_roll),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.user, channel=message.channel)

        if message.channel:
            if user is not None:
                text = "%s rolled a %s" % (user.name, random.randrange(1, 101))
            else:
                text = "%s rolled a %s" % (message.user, random.randrange(1, 101))
            callback.send_message(channel=message.channel, message=text, type_=message.type_)

    def high_roll(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.user, channel=message.channel)

        if message.channel:
            if user is not None:
                text = "%s rolled a %s" % (user.name, random.randrange(1, 10001))
            else:
                text = "%s rolled a %s" % (message.user, random.randrange(1, 10001))
            callback.send_message(channel=message.channel, message=text, type_=message.type_)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
