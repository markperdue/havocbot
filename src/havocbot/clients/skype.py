from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
import Skype4Py

logger = logging.getLogger(__name__)


class Skype(Client):

    @property
    def integration_name(self):
        return "skype"

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.username = None
        self.user_id = None
        self.exact_match_one_word_triggers = False

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        # for item in settings:
        #     # Switch on the key
        #     if item[0] == 'api_token':
        #         self.token = item[1]
        #         requirements_met = True
        #     elif item[0] == 'admins':
        #         pass

        # Set exact_match_one_word_triggers based off of value in havocbot if it is set
        settings_value = self.havocbot.get_havocbot_setting_by_name('exact_match_one_word_triggers')
        if settings_value is not None and settings_value.lower() == 'true':
            self.exact_match_one_word_triggers = True

        # Return true if this integrations has the information required to connect
        if requirements_met:
            return True
        else:
            logger.error("Skype configuration is not valid. Check your settings and try again")
            return False

    def connect(self):
        # Create an instance of the Skype class.
        self.client = Skype4Py.Skype()

        # Connect the Skype object to the Skype client.
        self.client.Attach()

        if self.client.CurrentUser is not None:
            # Set some values from the login_data response
            self.username = self.client.CurrentUser.FullName
            self.user_id = self.client.CurrentUser.Handle

            logger.info("I am.. %s! (%s)" % (self.username, self.user_id))
            return True
        else:
            return False

    def disconnect(self):
        if self.client is not None:
            self.client = None

    def debug_message(self, msg):
        logger.info("1 is '%s', 2 is '%s', 3 is '%s', 4 is '%s', 5 is '%s', 6 is '%s', 7 is '%s', 8 is '%s', 9 is '%s', 10 is '%s'" % (msg.Body, msg.Chat, msg.ChatName, msg.Datetime, msg.EditedBy, msg.EditedDatetime, msg.EditedTimestamp, msg.FromDisplayName, msg.FromHandle, msg.Id))
        # logger.info("11 is '%s', 12 is '%s', 13 is '%s', 14 is '%s'" % (msg.IsEditable, msg.LeaveReason, msg.MarkAsSeen, msg.Seen))
        logger.info("15 is '%s', 16 is '%s', 17 is '%s', 18 is '%s', 19 is '%s'" % (msg.Sender, msg.Status, msg.Timestamp, msg.Type, msg.Users))

    def process(self):
        self.client.OnMessageStatus = self.process_message

        # while not self.havocbot.should_shutdown:
        #     try:
        #         logger.info("To do")
        #     except AttributeError as e:
        #         logger.error("We have a problem! Is there a client?")
        #         logger.error(e)

    def process_message(self, msg, status):
        # Ignore messages originating from havocbot
        if msg.FromHandle is not None and msg.FromHandle != self.user_id and status == 'RECEIVED':
            message_object = Message(msg.Body, msg.FromHandle, msg.ChatName, msg.Type, 'skype', msg.Timestamp)
            logger.info("Received - %s" % (message_object))

            try:
                self.handle_message(message_object=message_object)
            except Exception as e:
                logger.error("Unable to handle the message")
                logger.error(e)
        else:
            logger.info('Ignoring message from self')
            # message_object = Message(msg.Body, msg.FromHandle, msg.ChatName, msg.Type, 'skype', msg.Timestamp)
            # logger.info("Received - %s" % (message_object))

            # try:
            #     self.handle_message(message_object=message_object)
            # except Exception as e:
            #     logger.error("Unable to handle the message")
            #     logger.error(e)

    def handle_message(self, **kwargs):
        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.event == 'SAID':
                for tuple_item in self.havocbot.triggers:
                    trigger = tuple_item[0]
                    triggered_function = tuple_item[1]

                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and self.exact_match_one_word_triggers is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            # logger.debug("Converting trigger to a line exact match requirement")
                            trigger = "^" + trigger + "$"

                    # Use trigger as regex pattern and then search the message for a match
                    regex = re.compile(trigger)

                    match = regex.search(message_object.text)
                    if match is not None:
                        logger.info("%s - Matched message against trigger '%s'" % (self.havocbot.get_method_class_name(triggered_function), trigger))

                        # Pass the message to the function associated with the trigger
                        try:
                            if len(tuple_item) == 2:
                                triggered_function(self, message_object, capture_groups=match.groups())
                            elif len(tuple_item) == 3:
                                additional_args = tuple_item[2]
                                triggered_function(self, message_object, capture_groups=match.groups(), **additional_args)
                        except Exception as e:
                            logger.error(e)
                    else:
                        logger.debug("Message did not match trigger '%s'" % (trigger))
                        pass
            else:
                logger.debug("Ignoring non message event of type '%s'" % (message_object.event))

    def get_chat_object_by_channel(self, channel):
        if self.client.Chats is not None:
            chat = next((obj for obj in self.client.Chats if channel == obj.Name), None)
            if chat is not None:
                return chat

        return None

    def send_message(self, text, channel, event=None, **kwargs):
        if channel and text:
            logger.info("Sending text '%s' to channel '%s'" % (text, channel))
            try:
                chat = self.get_chat_object_by_channel(channel)
                if chat is not None:
                    chat.SendMessage(text)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, text_list, channel, event=None, **kwargs):
        if channel and text_list:
            joined_message = "\n".join(text_list)
            logger.info("Sending text list '%s' to channel '%s'" % (joined_message, channel))
            try:
                chat = self.get_chat_object_by_channel(channel)
                if chat is not None:
                    chat.SendMessage(joined_message)
            except AttributeError as e:
                logger.error("Unable to send message. Are you connected? %s" % (e))
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_user_by_id(self, user_id, **kwargs):
        user = None

        api_result = self.client.User(user_id)
        user = create_user_object_from_skype_user_object(api_result)

        logger.debug("get_user_by_id - user is '%s'" % (user))
        if user is not None and user:
            return user
        else:
            return None

    def get_users_by_name(self, name, channel=None, event=None, **kwargs):
        results = []

        # # This will search for users only in the provided channel
        # if channel is not None and channel:
        #     skype_chat_object = self.client.Chat(channel)
        #     if skype_chat_object is not None and skype_chat_object:
        #         results = self._get_matching_users_from_chat_for_name(skype_chat_object, name)

        # This will search all chats that Skype is connected with
        chats = self.client.Chats
        if chats is not None and chats:
            for chat in chats:
                chat_result_list = self._get_matching_users_from_chat_for_name(chat, name)
                results.extend(chat_result_list)

        logger.debug("get_users_by_name returning with '%s'" % (results))
        return results

    def _get_matching_users_from_chat_for_name(self, skype_chat_object, name):
        results = []

        if skype_chat_object is not None and skype_chat_object:
            members = skype_chat_object.Members
            if members is not None and members:
                for member in members:
                    # logger.debug(member)
                    user = create_user_object_from_skype_user_object(member)
                    if user is not None:
                        if user.is_like_user(name):
                            results.append(user)

        return results

    def get_user_from_message(self, message_sender, channel=None, event=None, **kwargs):
        user = self.get_user_by_id(message_sender)
        if user is not None and user:
            return user
        else:
            return None

    def get_users_in_channel(self, channel, event=None, **kwargs):
        result_list = []

        if channel is not None and channel:
            skype_chat_object = self.client.Chat(channel)
            if skype_chat_object is not None and skype_chat_object:
                members = skype_chat_object.Members
                if members is not None and members:
                    for member in members:
                        # logger.debug(member)
                        user = create_user_object_from_skype_user_object(member)
                        if user is not None:
                            result_list.append(user)

        return result_list


def create_user_object_from_skype_user_object(skype_user_object):
    user = None

    if skype_user_object is not None:
        handle = None
        full_name = None
        aliases = None

        aliases_temp = skype_user_object.Aliases
        if aliases_temp is not None and aliases_temp:
            aliases = aliases_temp

        handle_temp = skype_user_object.Handle
        if handle_temp is not None and len(handle_temp) > 0:
            handle = handle_temp

        full_name_temp = skype_user_object.FullName
        if full_name_temp is not None and len(full_name_temp) > 0:
            full_name = full_name_temp

        if handle is not None and handle:
            user = create_user_object(handle, full_name, aliases)

    return user


# Returns a newly created user from a json source
def create_user_object(handle, name, aliases):
    client = 'skype'

    user = User(handle)
    user.aliases = aliases
    user.client = client
    user.name = name

    logger.debug("create_user_object - user is '%s'" % (user))
    return user
