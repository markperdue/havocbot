#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class HelpPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'basics of the bot'

    @property
    def plugin_short_name(self):
        return 'help'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!help', example=None, description='display basic help information'),
            Usage(command='!help plugins', example=None, description='list the enabled plugins'),
            Usage(command='!help plugin <plugin>', example='!help plugin user',
                  description='display detailed information about a specific plugin'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!help', function=self.trigger_default, param_dict=None, requires=None),
            Trigger(match='!help plugins', function=self.trigger_help_plugins, param_dict=None, requires=None),
            Trigger(match='!help plugin\s', function=self.trigger_help_plugin, param_dict=None, requires=None),
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
        client_message_list = ['HavocBot can help you with the following.']
        for usage_message in self.get_usage_lines_from_plugin_as_list(self.plugin_usages):
            client_message_list.append(usage_message)

        if message.to:
            client.send_messages_from_list(client_message_list, message.reply(), event=message.event)

    def trigger_help_plugins(self, client, message, **kwargs):
        client_message_list = []

        tuples_list = self.get_help_list_sorted()

        client_message_list.append('Loaded Plugins - ' + ', '.join([('%s (%s)' % (i[1], i[0])) for i in tuples_list]))
        client_message_list.append("Details about a specific plugin are available with '!help plugin <plugin>'")

        if message.to:
            client.send_messages_from_list(client_message_list, message.reply(), event=message.event)

    def trigger_help_plugin(self, client, message, **kwargs):
        client_message_list = []

        tuples_list = self.get_help_list_sorted()
        words = message.text.split()

        if len(words) >= 3:
            temp_list = []
            for word in words[2:]:
                temp_list += [item for item in tuples_list if word in [item[0], item[1]]]
            if temp_list is not None and temp_list:
                client_message_list = self.get_plugin_help_matching_list(temp_list)
            else:
                client_message_list.append('No matching plugins were found. Plugin names are listed at !help plugins')
        else:
            # Print the plugin short name with the regular name in parenthesis as a joined string
            plugin_string = ', '.join([('%s (%s)' % (i[1], i[0])) for i in tuples_list])
            client_message_list.append('Loaded Plugins - %s' % plugin_string)
            client_message_list.append("Details about a specific plugin are available with '!help plugin <plugin>'")

        if message.to:
            client.send_messages_from_list(client_message_list, message.reply(), event=message.event)

    def get_plugin_help_matching_list(self, tuples_list):
        new_list = []

        for (plugin_name, plugin_short_name, dictionary) in tuples_list:
            if dictionary is not None:
                if 'description' in dictionary:
                    new_list.append('%s (%s) - %s' % (plugin_short_name, plugin_name, dictionary['description']))
                if 'usage' in dictionary:
                    for item in self.get_usage_lines_from_plugin_as_list(dictionary['usage']):
                        new_list.append(item)
            else:
                new_list.append('%s %s' % (plugin_short_name, plugin_name))

        return new_list

    def get_usage_lines_from_plugin_as_list(self, usages_tuples):
        usage_list = []

        for (usage, example, description) in usages_tuples:
            if usage is not None:
                if description is not None:
                    if example is not None:
                        message = "    Usage: %s - %s - (example '%s')" % (usage, description, example)
                        usage_list.append(message)
                    else:
                        message = '    Usage: %s - %s' % (usage, description)
                        usage_list.append(message)
                else:
                    message = '    Usage: %s' % usage
                    usage_list.append(message)

        return usage_list

    def get_help_list_sorted(self):
        tuples_list = []

        for statefulplugin in self.havocbot.plugins_core:
            help_tuple_item = self.get_help_item_tuple(statefulplugin.handler)
            tuples_list.append(help_tuple_item)

        for statefulplugin in self.havocbot.plugins_custom:
            help_tuple_item = self.get_help_item_tuple(statefulplugin.handler)
            tuples_list.append(help_tuple_item)

        # Sort in place with the first item in the tuple being the key
        tuples_list.sort(key=lambda help_item: help_item[1])

        return tuples_list

    def get_help_item_tuple(self, plugin):
        """
        Returns a tuple that contains two items

        Returns:
            a tuple that contains two items
            First item is the name of the plugin as a string.
            Second item is a dictionary containing usage tuples, description, example, and the short name
        """
        help_tuple_item = ()

        if plugin is not None:
            # Capture the name of the plugin
            plugin_name = type(plugin).__name__
            plugin_short_name = plugin.plugin_short_name

            plugin_item_dictionary = {}

            if plugin.plugin_description is not None:
                plugin_item_dictionary['description'] = plugin.plugin_description

            # if plugin.plugin_short_name is not None:
            #     plugin_item_dictionary['short_name'] = plugin.plugin_short_name

            if plugin.plugin_usages is not None:
                plugin_item_dictionary['usage'] = plugin.plugin_usages

            help_tuple_item = (plugin_name, plugin_short_name, plugin_item_dictionary)

        return help_tuple_item


# Make this plugin available to HavocBot
havocbot_handler = HelpPlugin()
