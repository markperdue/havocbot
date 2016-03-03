#!/havocbot

import havocbot.user
from havocbot.plugin import HavocBotPlugin
import logging

logger = logging.getLogger(__name__)


class UserPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "user management"

    @property
    def plugin_short_name(self):
        return "user"

    @property
    def plugin_usages(self):
        return [
            ("!user <username>", "!user markaperdue", "get information on a user"),
            ("!adduser <name> <username>", "!adduser mark markaperdue", "add the user to the database"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!user\s(.*)", self.get_user),
            ("!adduser\s(.*)", self.add_user),
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
        pass

    def get_user(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()

        if len(words) <= 5:
            stasher = havocbot.user.UserStash.getInstance()
            temp_list = []
            for word in words:
                logger.info("Looking for user for '%s'" % (word))
                a_user = stasher.get_user(word)

                if a_user is not None:
                    temp_list.append(a_user.pprint())
                    temp_list.extend(a_user.get_plugin_data_strings_as_list())
                else:
                    temp_list.append("User %s was not found" % (word))
            callback.send_messages_from_list(channel=message.channel, message=temp_list, event=message.event)
        else:
            callback.send_message(channel=message.channel, message="Too many parameters. What are you trying to do?", event=message.event)

    def add_user(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()

        if len(words) == 2:
            stasher = havocbot.user.UserStash.getInstance()
            logger.info("Words are '%s' and '%s'" % (words[0], words[1]))
            validation = stasher.add_user(words[0], words[1])

            if validation is True:
                callback.send_message(channel=message.channel, message="User added", event=message.event)
            else:
                callback.send_message(channel=message.channel, message="That user already exists!", event=message.event)
        else:
            callback.send_message(channel=message.channel, message="Invalid parameters. Check the help option for usage", event=message.event)

# Make this plugin available to HavocBot
havocbot_handler = UserPlugin()
