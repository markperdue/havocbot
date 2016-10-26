#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class RestartPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "Restart the bot"

    @property
    def plugin_short_name(self):
        return "restart"

    @property
    def plugin_usages(self):
        return [
            Usage(command="!restart", example=None, description="shut it down!"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!restart", function=self.start, param_dict=None, requires="bot:admin"),
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

    def start(self, client, message, **kwargs):
        if message.to:
            text = 'Restarting the bot. Hang tight'
            client.send_message(text, message.to, event=message.event)

        self.havocbot.restart()


# Make this plugin available to HavocBot
havocbot_handler = RestartPlugin()
