#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)


class ReloadPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "reloads all plugins"

    @property
    def plugin_short_name(self):
        return "reload"

    @property
    def plugin_usages(self):
        return [
            ("!reload", None, "shutdown and start all the plugins"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!reload", self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        self.havocbot.reload_plugins()
        if message.channel:
            callback.send_message(channel=message.channel, message="Reloaded %d modules and discovered %s commands" % (len(self.havocbot.plugins_core) + len(self.havocbot.plugins_custom), len(self.havocbot.triggers)))


# Make this plugin available to HavocBot
havocbot_handler = ReloadPlugin()
