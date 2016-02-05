#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ReloadPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            "!reload": self.start
        }
        self.help = {
            "description": "reloads all plugins",
            "usage": (
                ("!reload", None, "shutdown and start all the plugins"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        self.havocbot.reload_plugins()
        if message.channel:
            callback.send_message(channel=message.channel, message="Reloaded %d modules and discovered %s commands" % (len(self.havocbot.plugins_core) + len(self.havocbot.plugins_custom), len(self.havocbot.triggers)))

# Make this plugin available to HavocBot
havocbot_handler = ReloadPlugin()
