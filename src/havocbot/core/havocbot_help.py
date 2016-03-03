#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)


class HelpPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "basics of the bot"

    @property
    def plugin_short_name(self):
        return "help"

    @property
    def plugin_usages(self):
        return [
            ("!help", None, "display basic help information"),
            ("!help plugins", None, "list the enabled plugins"),
            ("!help plugin <plugin>", None, "display detailed information about a specific plugin"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!help", self.start),
            ("!help plugins", self.help_plugins),
            ("!help plugin\s", self.help_plugin),
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

    def start(self, callback, message, **kwargs):
        callback_message_list = ["HavocBot can help you with the following."]
        for usage_message in self.get_usage_lines_from_plugin_as_list(self.plugin_usages):
            callback_message_list.append(usage_message)

        if message.channel:
            callback.send_messages_from_list(channel=message.channel, message=callback_message_list, event=message.event)

    def help_plugins(self, callback, message, **kwargs):
        callback_message_list = []

        tuples_list = self.get_help_list_sorted()

        callback_message_list.append("Loaded Plugins - " + ", ".join([("%s (%s)" % (i[1], i[0])) for i in tuples_list]))
        callback_message_list.append("Details about a specific plugin are available with '!help plugin <plugin>'")

        if message.channel:
            callback.send_messages_from_list(channel=message.channel, message=callback_message_list, event=message.event)

    def help_plugin(self, callback, message, **kwargs):
        callback_message_list = []

        tuples_list = self.get_help_list_sorted()
        words = message.text.split()

        if len(words) >= 3:
            temp_list = []
            for word in words[2:]:
                temp_list += [item for item in tuples_list if word in [item[0], item[1]]]
            if temp_list is not None and len(temp_list) > 0:
                callback_message_list = self.get_plugin_help_matching_list(temp_list)
            else:
                callback_message_list.append("No matching plugins were found. Plugin names are listed at !help plugins")
        else:
            # Print the plugin short name with the regular name in parenthesis as a joined string
            callback_message_list.append("Loaded Plugins - " + ", ".join([("%s (%s)" % (i[1], i[0])) for i in tuples_list]))
            callback_message_list.append("Details about a specific plugin are available with '!help plugin <plugin>'")

        if message.channel:
            callback.send_messages_from_list(channel=message.channel, message=callback_message_list, event=message.event)

    def get_plugin_help_matching_list(self, tuples_list):
        new_list = []

        for (plugin_name, plugin_short_name, dictionary) in tuples_list:
            if dictionary is not None:
                if 'description' in dictionary:
                    new_list.append("%s (%s) - %s" % (plugin_short_name, plugin_name, dictionary['description']))
                if 'usage' in dictionary:
                    for item in self.get_usage_lines_from_plugin_as_list(dictionary['usage']):
                        new_list.append(item)
            else:
                new_list.append("%s" % (plugin_short_name, plugin_name))

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
                        message = "    Usage: %s - %s" % (usage, description)
                        usage_list.append(message)
                else:
                    message = "    Usage: %s" % (usage)
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

    # Returns a tuple that contains two items. First item is the name of the plugin as a string. Second item is a dictionary containing usage tuples, description, example, and the short name
    def get_help_item_tuple(self, plugin):
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
