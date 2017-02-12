#!/havocbot

import logging
from havocbot.exceptions import FormattedMessageNotSentError
from havocbot.message import FormattedMessage
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.user import User, UserDataAlreadyExistsException, UserDataNotFoundException, UserDoesNotExist

logger = logging.getLogger(__name__)


class UserPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'user management'

    @property
    def plugin_short_name(self):
        return 'user'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!add-user <name> <username>', example='!add-user Mark mark@chat.hipchat.com',
                  description='add the user to the database'),
            Usage(command='!get-user <name>', example='!get-user mark', description='get information on a user'),
            Usage(command='!get-userid <user-id>', example='!get-userid 1',
                  description='get information on a user by id'),
            Usage(command='!add-alias <user-id> <alias>', example='!add-alias 1 the_enforcer',
                  description='adds an alias to a user'),
            Usage(command='!del-alias <user-id> <alias>', example='!del-alias 1 the_enforcer',
                  description='deletes an alias to a user'),
            Usage(command='!get-aliases <user-id>', example='!get-aliases 1', description='get all aliases of a user'),
            Usage(command='!add-permission <user-id> <permission>', example='!add-permission 1 bot:user',
                  description='adds a permission to a user'),
            Usage(command='!del-permission <user-id> <permission>', example='!del-permission 1 bot:user',
                  description='deletes a permission to a user'),
            Usage(command='!get-permission <user-id>', example='!get-permission 1',
                  description='get permissions of a user'),
            Usage(command='!add-points <user-id> <points>', example='!add-points 1 3',
                  description='adds points to a user'),
            Usage(command='!del-points <user-id> <points>', example='!del-points 1 50',
                  description='deletes points from a user'),
            Usage(command='!get-points <user-id>', example='!get-points 1', description='get points of a user'),
            Usage(command='!set-image <user-id> <image url>', example='!set-image 1 http://i.imgur.com/fYP9yGH.gifv',
                  description="set a user's image"),
            Usage(command='!users', example=None, description='get user info on all users in the channel'),
            Usage(command='!me', example=None, description='get information on you'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!add-user\s(.*)\s(.*)', function=self.trigger_add_user, requires='bot:admin'),
            Trigger(match='!get-user\s(.*)', function=self.trigger_get_user, requires=None),
            Trigger(match='!get-userid\s([0-9]+)', function=self.trigger_get_user_by_id, requires=None),
            Trigger(match='!add-alias\s([0-9]+)\s(.+)', function=self.trigger_add_alias, requires='bot:admin'),
            Trigger(match='!del-alias\s([0-9]+)\s(.+)', function=self.trigger_del_alias, requires='bot:admin'),
            Trigger(match='!get-alias\s([0-9]+)', function=self.trigger_get_alias, requires=None),
            Trigger(match='!add-permission\s([0-9]+)\s(.+)', function=self.trigger_add_perm, requires='bot:admin'),
            Trigger(match='!del-permission\s([0-9]+)\s(.+)', function=self.trigger_del_perm, requires='bot:admin'),
            Trigger(match='!get-permission\s([0-9]+)', function=self.trigger_get_permission, requires='bot:admin'),
            Trigger(match='!add-points\s([0-9]+)\s([0-9]+)', function=self.trigger_add_points, requires='bot:points'),
            Trigger(match='!del-points\s([0-9]+)\s([0-9]+)', function=self.trigger_del_points, requires='bot:points'),
            Trigger(match='!get-points\s([0-9]+)', function=self.trigger_get_points, requires='bot:points'),
            Trigger(match='!set-image\s([0-9]+)\s(.*)', function=self.trigger_set_image, requires='bot:admin'),
            Trigger(match='!users', function=self.trigger_get_users, requires=None),
            Trigger(match='!me', function=self.trigger_get_sender, requires=None),
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
        pass

    def trigger_add_user(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_name = capture[0]
        captured_username = capture[1]
        text = None

        if captured_name and captured_username:
            a_user = User(0)
            a_user.name = captured_name
            a_user.usernames = {client.integration_name: [captured_username]}

            try:
                self.havocbot.db.add_user(a_user)
            except UserDataAlreadyExistsException:
                text = 'That user already exists'
            else:
                text = 'User added'
            finally:
                client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Invalid parameters. Check the help option for usage'
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_user(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()

        matched_users = []

        if len(words) <= 3:
            for word in words:
                is_user_found = False

                if word.isdigit():
                    try:
                        a_user = self.havocbot.db.find_user_by_id(int(word))
                    except UserDoesNotExist:
                        text = 'That user does not exist'
                        client.send_message(text, message.reply(), event=message.event)
                    else:
                        matched_users.append(a_user)
                        is_user_found = True
                else:
                    users = self.havocbot.db.find_users_by_matching_string_for_client(word, client.integration_name)
                    if users is not None and users:
                        matched_users.extend(users)
                        is_user_found = True

                if not is_user_found:
                    text = 'User %s was not found' % word
                    client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            client.send_message(text, message.reply(), event=message.event)

        if matched_users:
            set_users = set(matched_users)
            if len(set_users) > 1:
                text = 'Found %d matching users' % (len(set_users))
                client.send_message(text, message.reply(), event=message.event)
            for user_object in set_users:

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
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])

        try:
            a_user = self.havocbot.db.find_user_by_id(captured_user_id)
        except UserDoesNotExist:
            text = 'That user does not exist'
            client.send_message(text, message.reply(), event=message.event)
        else:
            f_message = self._get_formatted_message(a_user)

            try:
                client.send_formatted_message(f_message, message.reply(), event=message.event, style='thumbnail')
            except FormattedMessageNotSentError:
                client.send_messages_from_list(a_user.get_user_info_as_list(), message.reply(), event=message.event)

    def trigger_add_alias(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_alias = capture[1]
        text = None

        try:
            self.havocbot.db.add_alias_to_user_id(captured_user_id, captured_alias)
        except UserDataAlreadyExistsException:
            text = 'That alias already exists'
        else:
            text = 'Alias added'
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_alias(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_alias = capture[1]
        text = None

        try:
            self.havocbot.db.del_alias_to_user_id(captured_user_id, captured_alias)
        except KeyError:
            text = 'That user has no aliases to delete'
        except UserDataNotFoundException:
            text = 'That alias was not found'
        else:
            text = 'Alias deleted'
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_alias(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        text = None

        try:
            a_user = self.havocbot.db.find_user_by_id(captured_user_id)
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            text = "%s's aliases: %s" % (a_user.name, a_user.get_aliases_as_string())
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_add_perm(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_permission = capture[1]
        text = None

        try:
            self.havocbot.db.add_permission_to_user_id(captured_user_id, captured_permission)
        except UserDataAlreadyExistsException:
            text = 'That permission already exists'
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            text = 'Permission added'
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_perm(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_permission = capture[1]
        text = None

        try:
            self.havocbot.db.del_permission_to_user_id(captured_user_id, captured_permission)
        except KeyError:
            text = 'That user has no permissions to delete'
        except UserDataNotFoundException:
            text = 'That user does not have that permission'
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            text = 'Permission deleted'
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_permission(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        text = None

        try:
            a_user = self.havocbot.db.find_user_by_id(captured_user_id)
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            if a_user.permissions is not None and a_user.permissions:
                text = "%s's permissions: %s" % (a_user.name, a_user.get_permissions_as_string())
            else:
                text = '%s has no permissions' % a_user.name
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_add_points(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_points = int(capture[1])
        text = None

        try:
            self.havocbot.db.add_points_to_user_id(captured_user_id, captured_points)
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            text = 'Points updated for user id %d' % captured_user_id
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_del_points(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_points = int(capture[1])
        text = None

        try:
            self.havocbot.db.del_points_to_user_id(captured_user_id, captured_points)
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            text = 'Points updated for user id %d' % captured_user_id
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_points(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        text = None

        try:
            a_user = self.havocbot.db.find_user_by_id(captured_user_id)
        except UserDoesNotExist:
            text = 'That user does not exist'
        else:
            if a_user.points is not None and a_user.points.isdigit():
                phrase = 'point' if a_user.points == 1 else 'points'
                text = '%s has %d %s' % (a_user.name, a_user.points, phrase)
            else:
                text = '%s has no points' % a_user.name
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_set_image(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_user_id = int(capture[0])
        captured_url = capture[1]
        text = None

        try:
            self.havocbot.db.set_image_for_user_id(captured_user_id, captured_url)
        except UserDoesNotExist:
            text = 'That user does not exist'
        except ValueError:
            text = 'An image url must be provided'
        else:
            text = 'User updated'
        finally:
            client.send_message(text, message.reply(), event=message.event)

    def trigger_get_sender(self, client, message, **kwargs):
        message_list = []

        try:
            user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        except UserDoesNotExist:
            user = client.get_user_from_message(message.sender, channel=message.to, event=message.event)
            user.current_username = message.sender
            logger.debug(user)
            message_list.extend(user.get_user_info_as_list())
        else:
            user.current_username = message.sender
            logger.debug(user)
            message_list.extend(user.get_user_info_as_list())

        if message_list is not None and message_list:
            f_message = self._get_formatted_message(user)

            try:
                client.send_formatted_message(f_message, message.reply(), event=message.event, style='thumbnail')
            except FormattedMessageNotSentError:
                client.send_messages_from_list(message_list, message.reply(), event=message.event)
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
                message_list.append('Found %d users' % (len(set_users)))
            for client_user_object in set_users:
                message_list.append('%s' % client_user_object.name)

        if message_list:
            client.send_messages_from_list(message_list, message.reply(), event=message.event)
        else:
            text = 'No users found'
            client.send_message(text, message.reply(), event=message.event)

    def _get_formatted_message(self, user):
        message = FormattedMessage(
            text='%s' % (', '.join(user.get_other_usernames_as_list())),
            fallback_text='%s' % (', '.join(user.get_other_usernames_as_list())),
            title='User %s (%s)' % (user.name, user.get_aliases_as_string()),
            thumbnail_url=user.image,
            attributes=[
                {'label': 'UID', 'value': str(user.user_id)},
                {'label': 'Points', 'value': str(user.points)}
            ]
        )

        if user.current_username is not None and user.current_username:
            message.attributes.insert(0, {'label': 'Username', 'value': str(user.current_username)})

        return message


# Make this plugin available to HavocBot
havocbot_handler = UserPlugin()
