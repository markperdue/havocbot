from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
import sleekxmpp

logger = logging.getLogger(__name__)


class XMPP(Client):

    @property
    def integration_name(self):
        return "xmpp"

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.token = None
        self.username = None
        self.room_name = None
        self.nickname = None
        self.server = None
        self.exact_match_one_word_triggers = True

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        for item in settings:
            # Switch on the key
            if item[0] == 'jabber_id':
                self.username = item[1]
            elif item[0] == 'password':
                self.password = item[1]
            elif item[0] == 'room_name':
                self.room_name = item[1]
            elif item[0] == 'nickname':
                self.nickname = item[1]
            elif item[0] == 'server':
                self.server = item[1]

        # Return true if this integrations has the information required to connect
        if self.username is not None and self.password is not None and self.room_name is not None and self.nickname is not None and self.server is not None:
            return True
        else:
            logger.error("XMPP configuration is not valid. Check your settings and try again")
            return False

    def connect(self):
        if self.username is None:
            logger.error("A XMPP username must be configured")
        if self.password is None:
            logger.error("A XMPP password must be configured")

        self.client = MUCBot(self, self.havocbot, self.username, self.password, self.room_name + "@" + self.server, self.nickname)

        self.client.register_plugin('xep_0030')  # Service Discovery
        self.client.register_plugin('xep_0045')  # Multi-User Chat
        self.client.register_plugin('xep_0199', {'keepalive': True, 'interval': 60})  # XMPP Ping set for a keepalive ping every 60 seconds

        if self.client.connect():
            logger.info("I am.. %s! (%s)" % (self.nickname, self.username))
            return True
        else:
            return False

    def disconnect(self):
        if self.client is not None:
            self.client.disconnect()

    def process(self):
        self.client.process(block=True)

    def handle_message(self, **kwargs):
        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.type_ == 'message':
                for (trigger, triggered_function) in self.havocbot.triggers:
                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and self.exact_match_one_word_triggers is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            logger.debug("Converting trigger to a line exact match requirement")
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

                        # No longer breaking on a match since it is possible for two plugins to match
                        # the same trigger and breaking would only allow one trigger to be matched
                        # break
                    else:
                        logger.debug("No match. Skipping '%s'" % (trigger))
                        pass
            else:
                logger.debug("Ignoring non message event of type '%s'" % (message_object.type_))

    def send_message(self, **kwargs):
        if kwargs is not None:
            if 'message' in kwargs and kwargs.get('message') is not None:
                message = kwargs.get('message')
            if 'channel' in kwargs and kwargs.get('channel') is not None:
                channel = kwargs.get('channel')

            if channel and message:
                logger.info("Sending message '%s' to channel '%s'" % (message, channel))
                try:
                    self.client.send_message(mto=channel, mbody=message, mtype='groupchat')
                except AttributeError:
                    logger.error("Unable to send message. Are you connected?")
                except Exception as e:
                    logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, **kwargs):
        if kwargs is not None:
            if 'message' in kwargs and kwargs.get('message') is not None:
                message = kwargs.get('message')
            if 'channel' in kwargs and kwargs.get('channel') is not None:
                channel = kwargs.get('channel')

            if channel and message:
                joined_message = "\n".join(message)
                logger.info("Sending message list '%s' to channel '%s'" % (joined_message, channel))
                try:
                    self.client.send_message(mto=channel, mbody=joined_message, mtype='groupchat')
                except AttributeError:
                    logger.error("Unable to send message. Are you connected?")
                except Exception as e:
                    logger.error("Unable to send message. %s" % (e))

    def get_user_by_id(self, name):
        room_full = "%s@%s" % (self.room_name, self.server)
        jabber_id = self.client.plugin['xep_0045'].getJidProperty(room_full, name, 'jid')

        user = create_user_object_from_json(name, jabber_id)

        if user:
            return user
        else:
            return None


class MUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, callback, havocbot, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.havocbot = havocbot
        self.parent = callback
        self.room = room
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)

    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

    def muc_message(self, msg):
        if msg['mucnick'] != self.nick:
            message_object = Message(msg['body'], msg['mucnick'], self.room, "message")
            logger.info("Received - %s" % (message_object))

            try:
                self.parent.handle_message(message_object=message_object)
            except Exception as e:
                logger.error(e)


class XMPPUser(User):
    def __init__(self, real_name, jabber_id):
        self.name = real_name
        self.username = jabber_id

    def __str__(self):
        return "XMPPUser(Name: '%s', Username: '%s')" % (self.name, self.username)


# Returns a newly created user from a json source
def create_user_object_from_json(name, jabber_id):
    user = XMPPUser(name, jabber_id)
    logger.debug(user)

    return user
