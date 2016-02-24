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
        self.exact_match_one_word_triggers = True

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
        if msg.FromHandle is not None and msg.FromHandle != self.user_id:
            message_object = Message(msg.Body, msg.FromHandle, msg.ChatName, msg.Type, msg.Timestamp)
            logger.info("Received - %s" % (message_object))

            try:
                self.handle_message(message_object=message_object)
            except Exception as e:
                logger.error("Unable to handle the message")
                logger.error(e)
        else:
            logger.info('Ignoring message from self')

    def handle_message(self, **kwargs):
        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.type_ == 'SAID':
                for (trigger, triggered_function) in self.havocbot.triggers:
                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and self.exact_match_one_word_triggers is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            # logger.debug("Converting trigger to a line exact match requirement")
                            trigger = "^" + trigger + "$"

                    # Use trigger as regex pattern and then search the message for a match
                    regex = re.compile(trigger)

                    match = regex.search(message_object.text)
                    if match is not None:
                        logger.info("Matched message against trigger '%s'" % (trigger))

                        # Pass the message to the function associated with the trigger
                        try:
                            triggered_function(self, message_object, capture_groups=match.groups())
                        except Exception as e:
                            logger.error(e)
                    else:
                        logger.debug("Message did not match trigger '%s'" % (trigger))
                        pass
            else:
                logger.debug("Ignoring non message event of type '%s'" % (message_object.type_))

    def get_chat_object_by_channel(self, channel):
        if self.client.Chats is not None:
            chat = next((obj for obj in self.client.Chats if channel == obj.Name), None)
            if chat is not None:
                return chat

        return None

    def send_message(self, message, channel, type_, **kwargs):
        if channel and message:
            logger.info("Sending message '%s' to channel '%s'" % (message, channel))
            try:
                chat = self.get_chat_object_by_channel(channel)
                if chat is not None:
                    chat.SendMessage(message)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, message, channel, type_, **kwargs):
        if channel and message:
            joined_message = "\n".join(message)
            logger.info("Sending message list '%s' to channel '%s'" % (joined_message, channel))
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

        if self.client:
            user_object = next((obj for obj in self.client.SearchForUsers(user_id) if user_id == obj.Handle), None)
            if user_object is not None:
                user = create_user_object_from_json(user_object.FullName, user_object.Handle)

        logger.debug("Returning user '%s'" % (user))
        return user


# Returns a newly created user from a json source
def create_user_object_from_json(name, handle):
    user = User(name, handle)
    logger.debug(user)

    return user
