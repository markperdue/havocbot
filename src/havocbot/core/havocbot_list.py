#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ListPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            "!list": self.start
        }
        self.help = {
            "description": "list available commands",
            "usage": (
                ("!list", None, "list available commands"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        if message.channel:
            callback.send_message(channel=message.channel, message="Available Commands: '" + "', '".join(self.havocbot.triggers.keys()) + "'")

# Make this plugin available to HavocBot
havocbot_handler = ListPlugin()
