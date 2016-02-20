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

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        if message.channel:
            callback.send_message(channel=message.channel, message="Available Commands: '" + "', '".join([(i[0]) for i in self.havocbot.triggers]) + "'", type_=message.type_)


# Make this plugin available to HavocBot
havocbot_handler = ListPlugin()
