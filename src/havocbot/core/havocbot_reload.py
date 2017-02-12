#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class ReloadPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'reloads all plugins'

    @property
    def plugin_short_name(self):
        return 'reload'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!reload', example=None, description='shutdown and start all the plugins'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!reload', function=self.trigger_default, param_dict=None, requires='bot:admin'),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot

    def configure(self, settings):
        requirements_met = True

        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        pass

    def trigger_default(self, client, message, **kwargs):
        self.havocbot.reload_plugins()

        plugin_count = len(self.havocbot.plugins_core) + len(self.havocbot.plugins_custom)

        text = 'Reloaded %d modules and discovered %s commands' % (plugin_count, len(self.havocbot.triggers))
        client.send_message(text, message.reply(), event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = ReloadPlugin()
