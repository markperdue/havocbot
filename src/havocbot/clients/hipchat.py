from dateutil import tz
from datetime import datetime
from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
import sleekxmpp

logger = logging.getLogger(__name__)


class HipChat(Client):

    @property
    def integration_name(self):
        return 'hipchat'

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.token = None
        self.username = None
        self.room_names = None
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
            elif item[0] == 'room_names':
                self.room_names = item[1].strip().split(',')
            elif item[0] == 'nickname':
                self.nickname = item[1]
            elif item[0] == 'server':
                self.server = item[1]

        # Return true if this integrations has the information required to connect
        if self.username is not None and self.password is not None and self.room_names is not None and self.nickname is not None and self.server is not None:
            # Make sure there is at least one non falsy room to join (ex. room_names = ,,,,,, should fail)
            if len([x for x in self.room_names if x]) > 0:
                logger.debug('There is at least one non falsy room name')
                return True
            else:
                logger.error('You must enter at least one chatroom in settings.ini for this configuration')
                return False
        else:
            logger.error('HipChat configuration is not valid. Check your settings and try again')
            return False

    def connect(self):
        if self.username is None:
            logger.error('A XMPP username must be configured')
        if self.password is None:
            logger.error('A XMPP password must be configured')

        self.client = HipMUCBot(self, self.havocbot, self.username, self.password, self.room_names, self.server, self.nickname)

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

            if message_object.type_ in ('groupchat', 'chat', 'normal'):
                for (trigger, triggered_function) in self.havocbot.triggers:
                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and self.exact_match_one_word_triggers is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            # logger.debug('Converting trigger to a line exact match requirement')
                            trigger = '^' + trigger + '$'

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

    def send_message(self, message, channel, type_, **kwargs):
        if channel and message and type_:
            logger.info("Sending %s message '%s' to channel '%s'" % (type_, message, channel))
            try:
                self.client.send_message(mto=channel, mbody=message, mtype=type_)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, message, channel, type_, **kwargs):
        if channel and message and type_:
            joined_message = '\n'.join(message)
            logger.info("Sending %s message list '%s' to channel '%s'" % (type_, joined_message, channel))
            try:
                self.client.send_message(mto=channel, mbody=joined_message, mtype=type_)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_user_by_id(self, name, **kwargs):
        user = None

        # Check to see if the name is already a JID
        jid_bare = getattr(name, 'bare', None)
        if jid_bare is not None:
            # JID already known
            user = create_user_object_from_json(name, jid_bare)
        else:
            # Fetch JID from xep_0045
            channel = kwargs.get('channel', None)
            if channel is not None and channel:
                if '@' not in channel:
                    channel = "%s@%s" % (channel, self.server)

                jabber_id = self.client.plugin['xep_0045'].getJidProperty(channel, name, 'jid')
                user = create_user_object_from_json(name, jabber_id.bare)

        return user

    # def get_user_by_id(self, name, **kwargs):
    #     room_full = "%s@%s" % (self.room_name, self.server)
    #     jabber_id = self.client.plugin['xep_0045'].getJidProperty(room_full, name, 'jid')

    #     user = create_user_object_from_json(name, jabber_id.bare)

    #     if user:
    #         return user
    #     else:
    #         return None


class HipMUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, callback, havocbot, jid, password, rooms_list, server_host, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid + '/bot', password)

        self.havocbot = havocbot
        self.parent = callback
        self.rooms = rooms_list
        self.nick = nick
        self.server_host = server_host

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)  # Also catches groupchat_message

    def start(self, event):
        self.get_roster()
        self.send_presence()
        for item in self.rooms:
            if len(item) > 0:
                room_string = item + '@' + self.server_host
                logger.debug("Joining room '%s'" % (room_string))
                self.plugin['xep_0045'].joinMUC(room_string, self.nick, wait=True)

    def log_msg(self, msg):
        if msg['type'] == 'groupchat':
            logger.info("Message - Type: '%s', To: '%s', From: '%s', ID: '%s', MUCNick: '%s', MUCRoom '%s', Body '%s'" % (msg['type'], msg['to'], msg['from'], msg['id'], msg['mucnick'], msg['mucroom'], msg['body']))
            if msg['subject'] and msg['thread']:
                logger.info("Message - Thread '%s', Body '%s'" % (msg['thread'], msg['body']))
        else:
            logger.info("Message - Type: '%s', To: '%s', From: '%s', ID: '%s', Body '%s'" % (msg['type'], msg['to'], msg['from'], msg['id'], msg['body']))
            if msg['subject'] and msg['thread']:
                logger.info("Message - Thread '%s', Body '%s'" % (msg['thread'], msg['body']))

    def message(self, msg):
        if msg['type'] == 'groupchat':
            if msg['mucnick'] != self.nick:
                message_object = Message(msg['body'], msg['mucnick'], msg['mucroom'], msg['type'], datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)
        elif msg['type'] in ('normal', 'chat'):
            if msg['from'].bare != self.boundjid.bare:
                message_object = Message(msg['body'], msg['from'], msg['from'], msg['type'], datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)


class HipChatUser(User):
    def __init__(self, real_name, jabber_id):
        self.name = real_name
        self.username = jabber_id

    def __str__(self):
        return "HipChatUser(Name: '%s', Username: '%s')" % (self.name, self.username)


# Returns a newly created user from a json source
def create_user_object_from_json(name, jabber_id):
    user = HipChatUser(name, jabber_id)
    logger.debug(user)

    return user
