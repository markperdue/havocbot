#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RestartPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "Restart the bot"

    @property
    def plugin_short_name(self):
        return "restart"

    @property
    def plugin_usages(self):
        return (
            ("!restart", None, "shut it down!"),
        )

    @property
    def plugin_triggers(self):
        return (
            ("!restart", self.start),
        )

    def init(self, havocbot):
        self.havocbot = havocbot

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        if message.channel:
            callback.send_message(channel=message.channel, message="Restarting the bot. Hang tight")
        self.havocbot.restart()


# Make this plugin available to HavocBot
havocbot_handler = RestartPlugin()
