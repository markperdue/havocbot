#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HelpPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            "!help": self.start,
            "!help plugins": self.help_plugins
        }
        self.help = {
            "description": "basics of the bot",
            "usage": (
                ("!help", None, "display basic help information"),
                ("!help plugins", None, "list the enabled plugins"),
                ("!help plugins <plugin>", None, "display detailed information about a specific plugin"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        callback_message_list = ["HavocBot can help you with the following.", "!help plugins - displays a list of plugins", "!help plugins <pluginname> - detailed information about a plugin"]

        callback.send_messages_from_list(channel=message.channel, message=callback_message_list)

    def process_usages(self, help_list, usages):
        for (usage, example, description) in usages:
            new_list = []
            new_list.append("    Usage: ")
            if usage is not None:
                new_list.append("'%s'" % (usage))
            if description is not None:
                new_list.append("%s" % (description))
            if example is not None:
                new_list.append(" (example '%s')" % (example))

            help_list.append(" - ".join(new_list))

    def get_message_list(self, tuples_list):
        new_list = []

        for (name, dictionary) in tuples_list:
            if dictionary is not None:
                if 'description' in dictionary:
                    new_list.append("%s - %s" % (name, dictionary['description']))
                if 'usage' in dictionary:
                    self.process_usages(new_list, dictionary['usage'])
            else:
                new_list.append("%s" % (name))

        return new_list

    def help_plugins(self, callback, message, **kwargs):
        tuples_list = self.get_help_list_sorted()

        words = message.text.split()
        callback_message_list = []

        if len(words) >= 3:
            temp_list = []
            for word in words[2:]:
                temp_list += [item for item in tuples_list if item[0] == word]
            if temp_list is not None and len(temp_list) > 0:
                callback_message_list = self.get_message_list(temp_list)
            else:
                callback_message_list = ["No matching plugins were found. Plugin names are listed at !help plugins"]
        else:
            # Print just the plugin names as a joined string
            callback_message_list = ["Loaded Plugins - " + ", ".join([(i[0]) for i in tuples_list])]

        callback.send_messages_from_list(channel=message.channel, message=callback_message_list)

    # Returns a tuple that contains two items. First item is the name of the plugin as a string. Second item is a dictionary containing usage, description, example, and trigger keys/values
    def get_help_item_tuple(self, plugin):
        help_tuple_item = ()

        if plugin is not None:
            # Capture the name of the plugin
            plugin_name = type(plugin).__name__

            plugin_item_dictionary = {}

            # Capture help dictionary
            if plugin.help is not None:
                plugin_item_dictionary = plugin.help

            # Capture trigger dictionary's keys and covert the list to a comma-separated string
            if plugin.triggers is not None:
                # logger.debug("%s" % (plugin.triggers.keys()))
                plugin_item_dictionary['triggers'] = ", ".join(plugin.triggers.keys())

            # help_dictionary_item[plugin_name] = plugin.help
            help_tuple_item = (plugin_name, plugin_item_dictionary)

        return help_tuple_item

    def get_help_list_sorted(self):
        tuples_list = []

        for statefulplugin in self.havocbot.plugins_core:
            help_tuple_item = self.get_help_item_tuple(statefulplugin.handler)
            tuples_list.append(help_tuple_item)

        for statefulplugin in self.havocbot.plugins_custom:
            help_tuple_item = self.get_help_item_tuple(statefulplugin.handler)
            tuples_list.append(help_tuple_item)

        # Sort in place with the first item in the tuple being the key
        tuples_list.sort(key=lambda help_item: help_item[0])

        return tuples_list

# Make this plugin available to HavocBot
havocbot_handler = HelpPlugin()
