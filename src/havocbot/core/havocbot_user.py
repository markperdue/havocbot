#!/havocbot

import havocbot.user
from havocbot.plugin import HavocBotPlugin
from havocbot.stasher import Stasher
import logging
import havocbot.exceptions as exceptions

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
            ("!user <name>", "!user mark", "get information on a user"),
            ("!userid <user_id>", "!user mark", "get information on a user by id"),
            ("!users", "!users", "get user info on all users in the channel"),
            ("!adduser <user_id>", "!adduser markaperdue", "add the user to the database"),
            ("!clientuser <name>", "!clientuser mark", "get information on a user from the chat client"),
            ("!stasheruser <name>", "!stasheruser mark", "get information on a user from local storage"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!user\s(.*)", self.trigger_get_user, {'stasher': True, 'client': True}),
            ("!userid\s(.*)", self.trigger_get_user, {'stasher': True, 'client': True, 'id': True}),
            ("!users", self.trigger_get_users),
            ("!adduser\s(.*)", self.trigger_add_user),
            ("!clientuser\s(.*)", self.trigger_get_user, {'client': True}),
            ("!stasheruser\s(.*)", self.trigger_get_user, {'stasher': True}),
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

    def trigger_get_user(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()
        use_stasher = kwargs.get('stasher', None)
        use_client = kwargs.get('client', None)
        use_id = kwargs.get('id', None)

        matched_users = []
        message_list = []

        if len(words) <= 3:
            for word in words:
                user_found = False

                if use_stasher is True:
                    stasher = Stasher.getInstance()
                    stasher_results = []

                    if use_id is True:
                        user_result = stasher.get_user_by_id(word)
                        if user_result is not None:
                            stasher_results = [user_result]
                    else:
                        stasher_results = stasher.get_users_by_name(word)

                    if stasher_results:
                        matched_users.extend(stasher_results)
                        user_found = True
                if use_client is True:
                    callback_results = []

                    if use_id is True:
                        user_result = callback.get_user_by_id(word)
                        if user_result is not None:
                            callback_results = [user_result]
                    else:
                        callback_results = callback.get_users_by_name(word)

                    if callback_results:
                        matched_users.extend(callback_results)
                        user_found = True

                if not user_found:
                    callback.send_message(
                        channel=message.channel,
                        message="User %s was not found" % (word),
                        event=message.event
                    )
        else:
            callback.send_message(
                channel=message.channel,
                message='Too many parameters. What are you trying to do?',
                event=message.event
            )

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                message_list.append(
                    "Found %d matching users" % (len(set_users))
                )
            for user_object in set_users:
                message_list.append(user_object.pprint())
                message_list.extend(
                    user_object.get_plugin_data_strings_as_list()
                )

        if message_list:
            callback.send_messages_from_list(
                channel=message.channel,
                message=message_list,
                event=message.event
            )

    def trigger_get_users(self, callback, message, **kwargs):
        matched_users = []
        message_list = []

        users = callback.get_users_in_channel(None)
        if users:
            for user_object in users:
                matched_users.append(user_object)

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                message_list.append("Found %d users" % (len(set_users)))
            for user_object in set_users:
                message_list.append(user_object.pprint())

        if message_list:
            callback.send_messages_from_list(
                channel=message.channel,
                message=message_list,
                event=message.event
            )
        else:
            callback.send_message(
                channel=message.channel,
                message='No users found',
                event=message.event
            )

    def trigger_add_user(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_values = capture[0].split()

        if captured_values:
            stasher = havocbot.Stasher.getInstance()
            logger.info("values are '%s'" % (captured_values))
            try:
                logger.info(
                    "about to get user by id '%s'" % (captured_values[0])
                )
                a_user = callback.get_user_by_id(captured_values[0])
                logger.info("a_user is '%s'" % (a_user))
                if a_user is not None and a_user.is_valid():
                    stasher.add_user(a_user)

                callback.send_message(
                    channel=message.channel,
                    message="User added",
                    event=message.event
                )
            except exceptions.StasherEntryAlreadyExistsError as e:
                logger.error(
                    "User alread exists - Existing user json is '%s'" % (e)
                )

                callback.send_message(
                    channel=message.channel,
                    message="That user already exists!",
                    event=message.event
                )
        else:
            callback.send_message(
                channel=message.channel,
                message="Invalid parameters. Check the help option for usage",
                event=message.event
            )

# Make this plugin available to HavocBot
havocbot_handler = UserPlugin()
