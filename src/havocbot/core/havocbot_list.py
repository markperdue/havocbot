#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)


class ListPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "list available commands"

    @property
    def plugin_short_name(self):
        return "list"

    @property
    def plugin_usages(self):
        return [
            ("!list", None, "list available commands"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!list", self.start),
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
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        if message.channel:
            callback.send_message(channel=message.channel, message="Available Commands: '" + "', '".join([(i[0]) for i in self.havocbot.triggers]) + "'", event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = ListPlugin()
