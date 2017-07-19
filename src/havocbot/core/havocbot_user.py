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
            Usage(command='!user add <name> <username>', example='!user add Mark mark@chat.hipchat.com',
                  description='add the user to the database'),
            Usage(command='!user get <name>', example='!user get mark', description='get information'),
            Usage(command='!user get-id <user-id>', example='!user get-id 1',
                  description='get information by id'),
            Usage(command='!user aliases get <user-id>', example='!user alias get 1 ',
                  description='get all aliases'),
            Usage(command='!user aliases add|remove <user-id> <alias>', example='!user alias add 1 the_enforcer',
                  description='add or remove aliases'),
            Usage(command='!user permissions get <user-id>', example='!user permissions get 1',
                  description='get permissions'),
            Usage(command='!user permissions add|remove <user-id> <permission>', example='!user permissions add 1 bot:user',
                  description='add or remove permissions'),
            Usage(command='!user points get <user-id>', example='!user points get 1', description='get points'),
            Usage(command='!user points add|remove <user-id> <points>', example='!user points add 1 3',
                  description='add or remove points'),
            Usage(command='!user image set <user-id> <image url>', example='!user image set 1 http://i.imgur.com/fYP9yGH.gifv',
                  description="set an image"),
            Usage(command='!user me', example=None, description='get information on you'),
            Usage(command='!users', example=None, description='get user info on all users in the channel'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!user add (.*) (.*)', function=self.trigger_add_user, requires='bot:admin'),
            Trigger(match='!user get (.*)', function=self.trigger_get_user, requires=None),
            Trigger(match='!user get-id ([0-9]+)', function=self.trigger_get_user_by_id, requires=None),
            Trigger(match='!user aliases add ([0-9]+) (.+)', function=self.trigger_add_alias, requires='bot:admin'),
            Trigger(match='!user aliases (rem|remove|del|delete) ([0-9]+) (.+)', function=self.trigger_del_alias, requires='bot:admin'),
            Trigger(match='!user aliases get ([0-9]+)', function=self.trigger_get_alias, requires=None),
            Trigger(match='!user permissions add ([0-9]+) (.+)', function=self.trigger_add_perm, requires='bot:admin'),
            Trigger(match='!user permissions (rem|remove|del|delete) ([0-9]+) (.+)', function=self.trigger_del_perm, requires='bot:admin'),
            Trigger(match='!user permissions get ([0-9]+)', function=self.trigger_get_permission, requires='bot:admin'),
            Trigger(match='!user points add ([0-9]+) ([0-9]+)', function=self.trigger_add_points, requires='bot:points'),
            Trigger(match='!user points (rem|remove|del|delete) ([0-9]+) ([0-9]+)', function=self.trigger_del_points, requires='bot:points'),
            Trigger(match='!user points get ([0-9]+)', function=self.trigger_get_points, requires='bot:points'),
            Trigger(match='!user image set ([0-9]+) (.*)', function=self.trigger_set_image, requires='bot:admin'),
            Trigger(match='!user me', function=self.trigger_get_sender, requires=None),
            Trigger(match='!users', function=self.trigger_get_users, requires=None),
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
        captured_user_id = int(capture[1])
        captured_alias = capture[2]
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
        captured_user_id = int(capture[1])
        captured_permission = capture[2]
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
        captured_user_id = int(capture[1])
        captured_points = int(capture[2])
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
