#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.stasher import Stasher

logger = logging.getLogger(__name__)


class InfoPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'info helper'

    @property
    def plugin_short_name(self):
        return 'info'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!info list', example=None, description='list all info categories'),
            Usage(command='!info get <info category>', example='!info get password',
                  description='get info on an info category'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!info list', function=self.trigger_info_list, param_dict=None, requires=None),
            Trigger(match='!info get\s(.*)', function=self.trigger_info_get, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.stasher = None

    def configure(self, settings):
        requirements_met = True

        self.stasher = Stasher.getInstance()
        self.stasher.plugin_data = self.stasher.get_plugin_data('havocbot_info')

        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def trigger_default(self, client, message, **kwargs):
        pass

    def get_category_for_printing(self, info_dict):
        results = []

        logger.info(info_dict)
        if info_dict is not None and info_dict:
            for item in info_dict:
                d_item = item['data'] if 'data' in item and item['data'] is not None and len(item['data']) > 0 else None
                n_item = item['name'] if 'name' in item and item['name'] is not None and len(item['name']) > 0 else None

                if d_item is not None and n_item is not None:
                    results.append('%s at %s' % (n_item, d_item))

        return results

    def trigger_info_get(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_category = capture[0]

        if len(captured_category) > 0:
            client_message_list = []
            info_data = self.stasher.plugin_data
            found_category = next((category for category in info_data['info']
                                   for (key, value) in category.items() if key.lower() == captured_category.lower()),
                                  None)
            if found_category is not None and found_category:
                client_message_list.extend(self.get_category_for_printing(found_category[captured_category]))

                client.send_messages_from_list(client_message_list, message.reply(), event=message.event)
            else:
                client.send_message("Unable to find '%s'" % captured_category, message.reply(), event=message.event)
        else:
            client.send_message('Please provide an info category', message.reply(), event=message.event)

    def trigger_info_list(self, client, message, **kwargs):
        client_message_list = []
        results = []

        info_data = self.stasher.plugin_data
        if 'info' in info_data and info_data['info'] is not None and info_data['info']:
            for category in info_data['info']:
                for (key, value) in category.items():
                    results.append(key)

        if results:
            categories_as_string = ', '.join(results)
            client_message_list.append('Info categories include %s' % categories_as_string)
            client_message_list.append('To get more info use !info get <category name>')

            client.send_messages_from_list(client_message_list, message.reply(), event=message.event)
        else:
            client.send_message('No info categories exist', message.reply(), event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = InfoPlugin()
