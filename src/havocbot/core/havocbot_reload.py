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

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        # self.havocbot = None  # start() still needs the reference to self.havocbot
        pass

    def start(self, callback, message, **kwargs):
        self.havocbot.reload_plugins()
        logger.info("Done with trigger reload_plugins()")
        if message.channel:
            callback.send_message(channel=message.channel, message="Reloaded %d modules and discovered %s commands" % (len(self.havocbot.plugins_core) + len(self.havocbot.plugins_custom), len(self.havocbot.triggers)), event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = ReloadPlugin()
