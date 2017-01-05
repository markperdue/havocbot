#!/havocbot

import logging
import traceback
from havocbot.exceptions import FormattedMessageNotSentError
from havocbot.message import FormattedMessage
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.user import User, UserDataAlreadyExistsException, UserDataNotFoundException

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
            Usage(command="!user add <name> <username>", example="!user add Mark mark@chat.hipchat.com", description="add the user to the database"),
            Usage(command="!user get <name>", example="!user get mark", description="get information on a user"),
            Usage(command="!user get-id <user-id>", example="!user get-id 1", description="get information on a user by id"),
            Usage(command="!user add-alias <user-id> <alias>", example="!user add-alias 1 the_enforcer", description="adds an alias to a user"),
            Usage(command="!user del-alias <user-id> <alias>", example="!user del-alias 1 the_enforcer", description="deletes an alias to a user"),
            Usage(command="!user get-aliases <user-id>", example="!user get-aliases 1", description="lists all aliases for a user"),
            Usage(command="!user add-permission <user-id> <permission>", example="!user add-permission 1 bot:user", description="adds a permission to a user"),
            Usage(command="!user del-permission <user-id> <permission>", example="!user del-permission 1 bot:user", description="deletes a permission to a user"),
            Usage(command="!user add-points <user-id> <points>", example="!user add-points 1 3", description="adds points to a user"),
            Usage(command="!user del-points <user-id> <points>", example="!user del-points 1 50", description="deletes points from a user"),
            Usage(command="!users", example=None, description="get user info on all users in the channel"),
            Usage(command="!me", example=None, description="get information on you"),
            # Usage(command="!clientuser <name>", example="!clientuser mark", description="get information on a user from the chat client"),
            # Usage(command="!stasheruser <name>", example="!stasheruser mark", description="get information on a user from local storage"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!user\sadd\s(.*)\s(.*)", function=self.trigger_add_user, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\sget\s(.*)", function=self.trigger_get_user, param_dict={'use_stasher': True, 'use_client': True}, requires=None),
            Trigger(match="!user\sget-id\s([0-9]+)", function=self.trigger_get_user_by_id, param_dict=None, requires=None),
            Trigger(match="!user\sadd-alias\s([0-9]+)\s(.+)", function=self.trigger_add_alias_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\sdel-alias\s([0-9]+)\s(.+)", function=self.trigger_del_alias_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\sget-aliases\s([0-9]+)", function=self.trigger_list_aliases_for_user_id, param_dict=None, requires=None),
            Trigger(match="!user\sadd-permission\s([0-9]+)\s(.+)", function=self.trigger_add_permission_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\sdel-permission\s([0-9]+)\s(.+)", function=self.trigger_del_permission_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\sadd-points\s([0-9]+)\s([0-9]+)", function=self.trigger_add_points_for_user_id, param_dict=None, requires="bot:points"),
            Trigger(match="!user\sdel-points\s([0-9]+)\s([0-9]+)", function=self.trigger_del_points_for_user_id, param_dict=None, requires="bot:points"),
            Trigger(match="!users", function=self.trigger_get_users, param_dict=None, requires=None),
            Trigger(match="!me", function=self.trigger_get_sender, param_dict=None, requires=None),
            # Trigger(match="!clientuser\s(.*)", function=self.trigger_coming_soon, param_dict={'use_client': True}, requires=None),
            # Trigger(match="!stasheruser\s(.*)", function=self.trigger_coming_soon, param_dict={'use_stasher': True}, requires=None),
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

    def trigger_default(self, client, message, **kwargs):
        pass

    def trigger_add_user(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_name = capture[0]
        captured_username = capture[1]

        if captured_name and captured_username:
            logger.info("values are '%s' and '%s'" % (captured_name, captured_username))

            a_user = User(0)
            a_user.name = captured_name
            a_user.usernames = {client.integration_name: [captured_username]}

            try:
                self.havocbot.db.add_user(a_user)
            except UserDataAlreadyExistsException:
                text = "That user already exists"
                client.send_message(text, message.reply(), event=message.event)
            else:
                text = "User added"
                client.send_message(text, message.reply(), event=message.event)
            # finally:
            #     client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Invalid parameters. Check the help option for usage'
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_user(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()

        matched_users = []

        if len(words) <= 3:
            for word in words:
                is_user_found = False

                users = self.havocbot.db.find_users_by_matching_string_for_client(word, client.integration_name)
                if users is not None and users:
                    matched_users.extend(users)
                    is_user_found = True

                if not is_user_found:
                    text = "User %s was not found" % (word)
                    client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            client.send_message(text, message.reply(), event=message.event)

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                text = "Found %d matching users" % (len(set_users))
                client.send_message(text, message.reply(), event=message.event)
                # message_list.append(text)
            for user_object in set_users:
                logger.debug("Matched User - '%s'" % (user_object))

                if user_object is not None:
                    fm = self._get_formatted_message(user_object)

                    try:
                        client.send_formatted_message(fm, message.reply(), event=message.event, style='thumbnail')
                    except FormattedMessageNotSentError:
                        client.send_messages_from_list(
                            user_object.get_user_info_as_list(),
                            message.reply(),
                            event=message.event
                        )

    def trigger_get_user_by_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])

        result = self.havocbot.db.find_user_by_id(captured_user_id)
        logger.info("Result here is '%s'" % (result))

        if result is not None and result:
            f_message = self._get_formatted_message(result)

            try:
                client.send_formatted_message(f_message, message.reply(), event=message.event, style='thumbnail')
            except FormattedMessageNotSentError:
                client.send_messages_from_list(
                    result.get_user_info_as_list(),
                    message.reply(),
                    event=message.event
                )
        else:
            text = "User ID %d was not found" % (captured_user_id)
            client.send_message(text, message.reply(), event=message.event)

    def trigger_add_alias_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_alias = capture[1]

        try:
            self.havocbot.db.add_alias_to_user_id(captured_user_id, captured_alias)
        except UserDataAlreadyExistsException:
            text = "That alias already exists"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Alias added"
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_alias_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_alias = capture[1]

        try:
            self.havocbot.db.del_alias_to_user_id(captured_user_id, captured_alias)
        except KeyError:
            text = "That user has no aliases to delete"
            client.send_message(text, message.reply(), event=message.event)
        except UserDataNotFoundException:
            text = "That alias was not found"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Alias deleted"
            client.send_message(text, message.reply(), event=message.event)

    def trigger_add_permission_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_permission = capture[1]

        try:
            self.havocbot.db.add_permission_to_user_id(captured_user_id, captured_permission)
        except UserDataAlreadyExistsException:
            text = "That permission already exists"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Permission added"
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_permission_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_permission = capture[1]

        try:
            self.havocbot.db.del_permission_to_user_id(captured_user_id, captured_permission)
        except KeyError:
            text = "That user has no permissions to delete"
            client.send_message(text, message.reply(), event=message.event)
        except UserDataNotFoundException:
            text = "That user does not have that permission"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Permission deleted"
            client.send_message(text, message.reply(), event=message.event)

    def trigger_add_points_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_points = int(capture[1])

        try:
            self.havocbot.db.add_points_to_user_id(captured_user_id, captured_points)
        except Exception as e:
            logger.error(traceback.format_exc())

            text = "Unable to add points to user id"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Points updated for user id %d" % (captured_user_id)
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_points_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_points = int(capture[1])

        try:
            self.havocbot.db.del_points_to_user_id(captured_user_id, captured_points)
        except Exception as e:
            logger.error(traceback.format_exc())
            text = "Unable to delete points from user id"
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "Points updated for user id %d" % (captured_user_id)
            client.send_message(text, message.reply(), event=message.event)

    def trigger_list_aliases_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])

        result = self.havocbot.db.find_user_by_id(captured_user_id)

        if result is not None and result:
            text = "%s's aliases: %s" % (result.name, result.get_aliases_as_string())
            client.send_message(text, message.reply(), event=message.event)
        else:
            text = "User ID %d was not found" % (captured_user_id)
            client.send_message(text, message.reply(), event=message.event)

    def trigger_coming_soon(self, client, message, **kwargs):
        text = 'This feature is coming soon'
        client.send_message(text, message.reply(), event=message.event)

    def trigger_get_sender(self, client, message, **kwargs):
        message_list = []
        
        user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        if user is not None and user:
            user.current_username = message.sender
            logger.debug(user)
            message_list.extend(user.get_user_info_as_list())
        else:
            user = client.get_user_from_message(message.sender, channel=message.to, event=message.event)
            user.current_username = message.sender
            logger.debug(user)
            message_list.extend(user.get_user_info_as_list())

        if message_list is not None and message_list:
            f_message = self._get_formatted_message(user)

            try:
                client.send_formatted_message(f_message, message.reply(), event=message.event, style='thumbnail')
            except FormattedMessageNotSentError:
                client.send_messages_from_list(
                    message_list,
                    message.reply(),
                    event=message.event
                )
        else:
            text = 'No matches found'
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_users(self, client, message, **kwargs):
        matched_users = []
        message_list = []

        users = client.get_users_in_channel(message.to, event=message.event)
        if users:
            for client_user_object in users:
                matched_users.append(client_user_object)

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                message_list.append("Found %d users" % (len(set_users)))
            for client_user_object in set_users:
                # message_list.extend(user_object.get_user_info_as_list())
                message_list.append("%s" % (client_user_object.name))
                # message_list.append(user_object.pprint())

        if message_list:
            client.send_messages_from_list(
                message_list,
                message.reply(),
                event=message.event
            )
        else:
            text = 'No users found'
            client.send_message(text, message.reply(), event=message.event)

    def _get_formatted_message(self, user):
        message = FormattedMessage(
            text="%s" % (', '.join(user.get_other_usernames_as_list())),
            fallback_text="%s" % (', '.join(user.get_other_usernames_as_list())),
            title="User %s (%s)" % (user.name, user.get_aliases_as_string()),
            thumbnail_url=user.image,
            attributes=[
                {"label": "UID", "value": str(user.user_id)},
                {"label": "Points", "value": str(user.points)}
            ]
        )

        if user.current_username is not None and user.current_username:
            message.attributes.insert(0, {"label": "Username", "value": str(user.current_username)})

        return message

    # def trigger_get_user(self, client, message, **kwargs):
    #     # Get the results of the capture
    #     capture = kwargs.get('capture_groups', None)
    #     captured_usernames = capture[0]
    #     words = captured_usernames.split()
    #     # use_stasher = kwargs.get('stasher', None)
    #     # use_client = kwargs.get('client', None)
    #     # use_id = kwargs.get('id', None)

    #     matched_users = []
    #     message_list = []

    #     if len(words) <= 3:
    #         for word in words:
    #             is_user_found = False

    #             user = havocbot.user.find_user_by_id_or_name(word, None, client)
    #             if user is not None and user:
    #                 matched_users.append(user)
    #                 is_user_found = True

    #             # user = havocbot.user.find_user_by_usernames(word, client)
    #             # if user is not None and user:
    #             #     matched_users.append(user)
    #             #     is_user_found = True

    #             # user = havocbot.user.find_user_by_id(word, client)
    #             # if user is not None and user:
    #             #     matched_users.append(user)
    #             #     is_user_found = True

    #             # users = havocbot.user.find_users_by_name(word, message.client)
    #             # if users:
    #             #     matched_users.extend(users)
    #             #     is_user_found = True

    #             if not is_user_found:
    #                 text = "User %s was not found" % (word)
    #                 client.send_message(text, message.reply(), event=message.event)

    #             # if use_stasher is True:
    #             #     stasher = Stasher.getInstance()
    #             #     stasher_results = []

    #             #     if use_id is True:
    #             #         user_result = stasher.get_user_by_id(word)
    #             #         if user_result is not None:
    #             #             stasher_results = [user_result]
    #             #     else:
    #             #         stasher_results = stasher.get_users_by_name(word, message.client)

    #             #     if stasher_results:
    #             #         matched_users.extend(stasher_results)
    #             #         user_found = True
    #             # if use_client is True:
    #             #     client_results = []

    #             #     if use_id is True:
    #             #         user_result = client.get_user_by_id(word)
    #             #         if user_result is not None:
    #             #             client_results = [user_result]
    #             #     else:
    #             #         client_results = client.get_users_by_name(word, channel=message.to, event=message.event)

    #             #     if client_results:
    #             #         matched_users.extend(client_results)
    #             #         user_found = True

    #             # if not user_found:
    #             #     text = "User %s was not found" % (word)
    #             #     client.send_message(text, message.reply(), event=message.event)
    #     else:
    #         text = 'Too many parameters. What are you trying to do?'
    #         client.send_message(text, message.reply(), event=message.event)

    #     if matched_users:
    #         set_users = set(matched_users)
    #         if len(set_users) > 1:
    #             message_list.append(
    #                 "Found %d matching users" % (len(set_users))
    #             )
    #         for user_object in set_users:
    #             message_list.append(user_object.pprint())
    #             message_list.extend(user_object.get_usernames_as_list())
    #             message_list.extend(
    #                 user_object.get_plugin_data_strings_as_list()
    #             )

    #     if message_list:
    #         client.send_messages_from_list(
    #             message_list,
    #             message.reply(),
    #             event=message.event
    #         )

    # def trigger_get_user_orig(self, client, message, **kwargs):
    #     # Get the results of the capture
    #     capture = kwargs.get('capture_groups', None)
    #     captured_usernames = capture[0]
    #     words = captured_usernames.split()
    #     use_stasher = kwargs.get('stasher', None)
    #     use_client = kwargs.get('client', None)
    #     use_id = kwargs.get('id', None)

    #     matched_users = []
    #     message_list = []

    #     if len(words) <= 3:
    #         for word in words:
    #             user_found = False

    #             if use_stasher is True:
    #                 stasher = Stasher.getInstance()
    #                 stasher_results = []

    #                 if use_id is True:
    #                     user_result = stasher.get_user_by_id(word)
    #                     if user_result is not None:
    #                         stasher_results = [user_result]
    #                 else:
    #                     stasher_results = stasher.get_users_by_name(word, message.client)

    #                 if stasher_results:
    #                     matched_users.extend(stasher_results)
    #                     user_found = True
    #             if use_client is True:
    #                 client_results = []

    #                 if use_id is True:
    #                     user_result = client.get_user_by_id(word)
    #                     if user_result is not None:
    #                         client_results = [user_result]
    #                 else:
    #                     client_results = client.get_users_by_name(word, channel=message.to, event=message.event)

    #                 if client_results:
    #                     matched_users.extend(client_results)
    #                     user_found = True

    #             if not user_found:
    #                 text = "User %s was not found" % (word)
    #                 client.send_message(text, message.reply(), event=message.event)
    #     else:
    #         text = 'Too many parameters. What are you trying to do?'
    #         client.send_message(text, message.reply(), event=message.event)

    #     if matched_users:
    #         set_users = set(matched_users)
    #         if len(set_users) > 1:
    #             message_list.append(
    #                 "Found %d matching users" % (len(set_users))
    #             )
    #         for user_object in set_users:
    #             message_list.append(user_object.pprint())
    #             message_list.extend(user_object.get_usernames_as_list())
    #             message_list.extend(
    #                 user_object.get_plugin_data_strings_as_list()
    #             )

    #     if message_list:
    #         client.send_messages_from_list(
    #             message_list,
    #             message.reply(),
    #             event=message.event
    #         )

# Make this plugin available to HavocBot
havocbot_handler = UserPlugin()
