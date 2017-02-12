#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class ListPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'list available commands'

    @property
    def plugin_short_name(self):
        return 'list'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!list', example=None, description='list available commands'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!list', function=self.trigger_default, param_dict=None, requires=None),
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
        self.havocbot = None

    def trigger_default(self, client, message, **kwargs):
        text = "Available Commands: '" + "', '".join([(i[0]) for i in self.havocbot.triggers]) + "'"
        client.send_message(text, message.reply(), event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = ListPlugin()
