#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.stasher import Stasher

logger = logging.getLogger(__name__)


class InfoPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "info helper"

    @property
    def plugin_short_name(self):
        return "info"

    @property
    def plugin_usages(self):
        return [
            Usage(command="!info list", example=None, description="list all info catagories"),
            Usage(command="!info get <info category>", example="!info get password", description="get info on an info catagory"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!info list", function=self.info_list, param_dict=None, requires=None),
            Trigger(match="!info get\s(.*)", function=self.info_get, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.stasher = None

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        self.stasher = Stasher.getInstance()
        self.stasher.plugin_data = self.stasher.get_plugin_data('havocbot_info')

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, client, message, **kwargs):
        pass

    def get_category_for_printing(self, info_dict):
        results = []

        logger.info(info_dict)
        if info_dict is not None and info_dict:
            for item in info_dict:
                # logger.info("item is '%s'" % (item))
                data_item = item['data'] if 'data' in item and item['data'] is not None and len(item['data']) > 0 else None
                name_item = item['name'] if 'name' in item and item['name'] is not None and len(item['name']) > 0 else None

                if data_item is not None and name_item is not None:
                    results.append("%s at %s" % (name_item, data_item))

        return results

    def info_get(self, client, message, **kwargs):
        logger.debug("start - message is '%s'" % (message))

        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_category = capture[0]

        if len(captured_category) > 0:
            client_message_list = []
            info_data = self.stasher.plugin_data
            # logger.info("info_data is '%s'" % (info_data))
            # logger.info("captured_category set to '%s'" % (captured_category))
            found_category = next((category for category in info_data['info'] for (key, value) in category.items() if key.lower() == captured_category.lower()), None)
            # logger.info("found category is '%s'" % (found_category))
            if found_category is not None and found_category:
                client_message_list.extend(self.get_category_for_printing(found_category[captured_category]))

                client.send_messages_from_list(client_message_list, message.to, event=message.event)
            else:
                client.send_message("Unable to find info category '%s'" % (captured_category), message.to, event=message.event)
        else:
            client.send_message('Please provide an info category', message.to, event=message.event)

    def info_list(self, client, message, **kwargs):
        logger.debug("start - message is '%s'" % (message))

        client_message_list = []
        results = []

        info_data = self.stasher.plugin_data
        if 'info' in info_data and info_data['info'] is not None and info_data['info']:
            for category in info_data['info']:
                logger.info("Category is '%s'" % (category))
                for (key, value) in category.items():
                    results.append(key)
                    logger.info("key is '%s', value is '%s'" % (key, value))

        if results:
            categories_as_string = ', '.join(results)
            client_message_list.append("Info categories include %s" % (categories_as_string))
            client_message_list.append('To get more info use !info get <category name>')

            client.send_messages_from_list(client_message_list, message.to, event=message.event)
        else:
            client.send_message('No info categories exist', message.to, event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = InfoPlugin()
