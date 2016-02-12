#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ShutdownPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "Shutdown the bot"

    @property
    def plugin_short_name(self):
        return "shutdown"

    @property
    def plugin_usages(self):
        return [
            ("!shutdown", None, "shut it down!"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!shutdown", self.start),
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
            callback.send_message(channel=message.channel, message="Shutting it down. Bye")
        self.havocbot.shutdown()


# Make this plugin available to HavocBot
havocbot_handler = ShutdownPlugin()
