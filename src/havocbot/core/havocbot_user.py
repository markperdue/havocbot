#!/havocbot

import logging
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

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
            Usage(command="!user get <name>", example="!user get mark", description="get information on a user"),
            Usage(command="!userid <user_id>", example="!userid 1", description="get information on a user by id"),
            Usage(command="!users", example=None, description="get user info on all users in the channel"),
            Usage(command="!adduser <user_id>", example="!adduser markaperdue", description="add the user to the database"),
            Usage(command="!clientuser <name>", example="!clientuser mark", description="get information on a user from the chat client"),
            Usage(command="!stasheruser <name>", example="!stasheruser mark", description="get information on a user from local storage"),
            Usage(command="!me", example=None, description="get information on you"),
            Usage(command="!user <user_id> add_alias <alias>", example="!user 1 add_alias the_enforcer", description="adds an alias to a user"),
            Usage(command="!user <user_id> del_alias <alias>", example="!user 1 del_alias the_enforcer", description="deletes an alias to a user"),
            Usage(command="!user <user_id> list_aliases", example="!user 1 get_aliases", description="lists any aliases to a user"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!user\sget(.*)", function=self.trigger_get_user, param_dict={'use_stasher': True, 'use_client': True}, requires=None),
            Trigger(match="!userid\s([0-9]+)", function=self.find_user_by_id, param_dict=None, requires=None),
            Trigger(match="!users", function=self.trigger_get_users, param_dict=None, requires=None),
            Trigger(match="!adduser\s(.*)", function=self.trigger_coming_soon, param_dict=None, requires="bot:admin"),
            Trigger(match="!clientuser\s(.*)", function=self.trigger_coming_soon, param_dict={'use_client': True}, requires=None),
            Trigger(match="!stasheruser\s(.*)", function=self.trigger_coming_soon, param_dict={'use_stasher': True}, requires=None),
            Trigger(match="!me", function=self.trigger_get_sender, param_dict=None, requires=None),
            Trigger(match="!user\s([0-9]+)\sadd_alias\s(.+)", function=self.add_alias_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\s([0-9]+)\sdel_alias\s(.+)", function=self.del_alias_for_user_id, param_dict=None, requires="bot:admin"),
            Trigger(match="!user\s([0-9]+)\slist_aliases\s(.+)", function=self.list_aliases_for_user_id, param_dict=None, requires=None),
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
        pass

    def find_user_by_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = capture[0]

        result = self.havocbot.db.find_user_by_id(int(captured_user_id))
        logger.info("Result here is '%s'" % (result))

    def add_alias_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = capture[0]
        captured_alias = capture[1]

        a_user = self.havocbot.db.find_user_by_id(captured_user_id)

        if a_user is not None and a_user:
            a_user.add_alias(captured_alias)
            a_user.save()

    def del_alias_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = capture[0]
        captured_alias = capture[1]

        a_user = self.havocbot.db.find_user_by_id(captured_user_id)

        if a_user is not None and a_user:
            a_user.del_alias(captured_alias)
            a_user.save()

    def list_aliases_for_user_id(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_user_id = capture[0]
        captured_alias = capture[1]

    def trigger_coming_soon(self, client, message, **kwargs):
        text = 'This feature is coming soon'
        client.send_message(text, message.reply(), event=message.event)

    def trigger_get_sender(self, client, message, **kwargs):
        message_list = []
        
        user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        if user is not None and user:
            logger.debug(user)
            message_list.extend(user.get_user_info_as_list())
        else:
            message_list.extend(client_user_object.get_user_info_as_list())

        # client_user_object = client.get_user_from_message(message.sender, channel=message.to, event=message.event)
        # logger.debug(client_user_object)

        # if client_user_object is not None and client_user_object:
        #     username = client_user_object.username
        #     message_list = []

        #     # EDIT101
        #     # user_temp_list = havocbot.user.get_users_by_username(username, client.integration_name)
        #     # if user_temp_list is not None and user_temp_list:
        #     #     for user in user_temp_list:
        #     #         logger.debug(user)
        #     #         # Update the user to have the previous username set
        #     #         user.current_username = username
        #     #         message_list.extend(user.get_user_info_as_list())
        #     # else:
        #     #     message_list.extend(client_user_object.get_user_info_as_list())

        #     user = havocbot.user.get_user_by_username_for_client(username, client.integration_name)
        #     if user is not None and user:
        #         logger.debug(user)
        #         # Update the user to have the previous username set
        #         user.current_username = username
        #         message_list.extend(user.get_user_info_as_list())
        #     else:
        #         message_list.extend(client_user_object.get_user_info_as_list())

        if message_list is not None and message_list:
            client.send_messages_from_list(
                message_list,
                message.reply(),
                event=message.event
            )
        else:
            text = 'No matches found'
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_user(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()
        # use_stasher = kwargs.get('stasher', None)
        # use_client = kwargs.get('client', None)
        # use_id = kwargs.get('id', None)

        matched_users = []
        matched_users_other_client = []
        message_list = []

        if len(words) <= 3:
            for word in words:
                is_user_found = False

                # user = havocbot.user.find_user_by_id_or_name(word, None, client)
                # if user is not None and user:
                #     matched_users.append(user)
                #     is_user_found = True

                # # TEST TO GET CLIENTUSER ONLY
                # client_user = client.get_user_from_message(message.sender, message.to, message.event)
                # logger.info('Client user is...')
                # logger.info(client_user)    

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
                message_list.append(
                    "Found %d matching users" % (len(set_users))
                )
            for user_object in set_users:
                logger.debug("Matched User - '%s'" % (user_object))
                if user_object is not None:
                    message_list.extend(user_object.get_user_info_as_list())
                # message_list.extend(user_object.get_usernames_as_list())
                # message_list.extend(
                #     user_object.get_plugin_data_strings_as_list()
                # )

        if message_list:
            client.send_messages_from_list(
                message_list,
                message.reply(),
                event=message.event
            )

    def trigger_get_users(self, client, message, **kwargs):
        matched_users = []
        message_list = []

        users = client.get_users_in_channel(message.to, event=message.event)
        if users:
            for user_object in users:
                matched_users.append(user_object)

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                message_list.append("Found %d users" % (len(set_users)))
            for user_object in set_users:
                # message_list.extend(user_object.get_user_info_as_list())
                message_list.append("%s %s" % (user_object.name, user_object.email))
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

    def trigger_add_user(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_values = capture[0].split()

        if captured_values:
            stasher = StasherDB.getInstance()
            logger.info("values are '%s'" % (captured_values))
            # try:
            #     logger.info(
            #         "about to get user by id '%s'" % (captured_values[0])
            #     )
            #     a_user = client.get_user_by_id(captured_values[0])
            #     logger.info("a_user is '%s'" % (a_user))
            #     if a_user is not None and a_user.is_valid():
            #         stasher.add_user(a_user)

            #     text = 'User added'
            #     client.send_message(text, message.reply(), event=message.event)
            # except exceptions.StasherEntryAlreadyExistsError as e:
            #     logger.error(
            #         "User alread exists - Existing user json is '%s'" % (e)
            #     )

            #     text = 'That user already exists!'
            #     client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Invalid parameters. Check the help option for usage'
            client.send_message(text, message.reply(), event=message.event)

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
