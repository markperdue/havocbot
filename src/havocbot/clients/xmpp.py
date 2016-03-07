from dateutil import tz
from datetime import datetime
from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
import sleekxmpp
# import ssl

logger = logging.getLogger(__name__)


class XMPP(Client):

    @property
    def integration_name(self):
        return 'xmpp'

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.token = None
        self.username = None
        self.room_names = None
        self.nickname = None
        self.server = None
        self.exact_match_one_word_triggers = False

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
            elif item[0] == 'chat_server':
                self.chat_server = item[1]

        # Set exact_match_one_word_triggers based off of value in havocbot if it is set
        settings_value = self.havocbot.get_havocbot_setting_by_name('exact_match_one_word_triggers')
        if settings_value is not None and settings_value.lower() == 'true':
            self.exact_match_one_word_triggers = True

        # Return true if this integrations has the information required to connect
        if self.username is not None and self.password is not None and self.room_names is not None and self.nickname is not None and self.server is not None and self.chat_server is not None:
            # Make sure there is at least one non falsy room to join (ex. room_names = ,,,,,, should fail)
            if len([x for x in self.room_names if x]) > 0:
                logger.debug('There is at least one non falsy room name')
                return True
            else:
                logger.error('You must enter at least one chatroom in settings.ini for this configuration')
                return False
        else:
            logger.error('XMPP configuration is not valid. Check your settings and try again')
            return False

    def connect(self):
        if self.username is None:
            logger.error('A XMPP username must be configured')
        if self.password is None:
            logger.error('A XMPP password must be configured')

        self.client = MUCBot(self, self.havocbot, self.username, self.password, self.room_names, self.server, self.nickname, self.chat_server)

        self.client.register_plugin('xep_0030')  # Service Discovery
        self.client.register_plugin('xep_0045')  # Multi-User Chat
        self.client.register_plugin('xep_0054')  # vCard
        self.client.register_plugin('xep_0199', {'keepalive': True, 'interval': 60})  # XMPP Ping set for a keepalive ping every 60 seconds

        # self.client.ssl_version = ssl.PROTOCOL_SSLv23

        # if self.client.connect(address=(self.server, 5223), use_ssl=True):
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

            if message_object.event in ('groupchat', 'chat', 'normal'):
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

    def send_message(self, message, channel, event, **kwargs):
        if channel and message and event:
            logger.info("Sending %s message '%s' to channel '%s'" % (event, message, channel))
            try:
                self.client.send_message(mto=channel, mbody=message, mtype=event)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, message, channel, event, **kwargs):
        if channel and message and event:
            joined_message = '\n'.join(message)
            logger.info("Sending %s message list '%s' to channel '%s'" % (event, joined_message, channel))
            try:
                self.client.send_message(mto=channel, mbody=joined_message, mtype=event)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_vcard_by_jabber_id(self, jabber_id):
        vcard = None

        if jabber_id is not None:
            if isinstance(jabber_id, sleekxmpp.jid.JID):
                bare_jid = jabber_id.bare
            else:
                bare_jid = jabber_id

            try:
                vcard = self.client.plugin['xep_0054'].get_vcard(jid=bare_jid)
            except sleekxmpp.exceptions.IqError as e:
                logger.error("IqError - %s" % (e.iq))
            except sleekxmpp.exceptions.IqTimeout:
                logger.error('IqTimeOut')

            return vcard

    def get_user_by_id(self, jabber_id, **kwargs):
        user = None

        # Arrive here commonly through private messages
        if isinstance(jabber_id, sleekxmpp.jid.JID):
            vcard = self.get_vcard_by_jabber_id(jabber_id)
            if vcard is not None:
                user = create_user_object_from_jid_and_vcard(jabber_id, vcard)
        # Arrive here commonly through group messages
        else:
            # Fallback to trying to get a user object from a name
            user = self.get_user_by_name(jabber_id, **kwargs)

        logger.debug("get_user_by_id - user is '%s'" % (user))
        if user is not None:
            return user
        else:
            return None

    def get_users_by_name(self, name, channel=None, **kwargs):
        results = []

        # Fetch JID from xep_0045
        # channel = kwargs.get('channel', None)
        if channel is not None and channel:
            if '@' not in channel:
                channel = "%s@%s" % (channel, self.server)

            jabber_id = self.client.plugin['xep_0045'].getJidProperty(channel, name, 'jid')

            if jabber_id is not None and jabber_id.bare is not None and jabber_id.bare:
                user = create_user_object(jabber_id.bare, name, None)
                results.append(user)

        logger.debug("get_users_by_name returning with '%s'" % (results))
        return results

    def get_user_by_name(self, name, **kwargs):
        user = None

        # Fetch JID from xep_0045
        channel = kwargs.get('channel', None)
        if channel is not None and channel:
            if '@' not in channel:
                channel = "%s@%s" % (channel, self.server)

            jabber_id = self.client.plugin['xep_0045'].getJidProperty(channel, name, 'jid')

            if jabber_id is not None and jabber_id.bare is not None and jabber_id.bare:
                user = create_user_object(jabber_id.bare, name, None)

        logger.debug("get_user_by_name - user is '%s'" % (user))
        if user is not None:
            return user
        else:
            return XMPPUser(name, name, name)

    def get_users_in_channel(self, team, **kwargs):
        result_list = []

        # TODO

        return result_list


class MUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, callback, havocbot, jid, password, rooms_list, server_host, nick, chat_server):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.havocbot = havocbot
        self.parent = callback
        self.rooms = rooms_list
        self.nick = nick
        self.server_host = server_host
        self.chat_server = chat_server

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)  # Also catches groupchat_message

    def start(self, event):
        self.get_roster()
        self.send_presence()
        for item in self.rooms:
            if len(item) > 0:
                room_string = item + '@' + self.chat_server
                logger.debug("Joining room '%s'" % (room_string))
                self.plugin['xep_0045'].joinMUC(room_string, self.nick, wait=True)

    def log_msg(self, msg):
        logger.debug(type(msg['from']))
        logger.debug(msg['from'].resource)
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


class XMPPUser(User):
    def __init__(self, user_id, name, email):
        super(XMPPUser, self).__init__(user_id)
        self.user_id = user_id
        self.name = name
        self.email = email

    def __str__(self):
        return "XMPPUser(User ID: '%s', Name: '%s', Email: '%s')" % (self.user_id, self.name, self.email)


# Returns a newly created user from a json source
def create_user_object(jabber_id, name, email):
    user = XMPPUser(jabber_id, name, email)

    logger.debug("create_user_object - user is '%s'" % (user))
    return user


# Returns a newly created user from a json source
def create_user_object_from_jid_and_vcard(jabber_id, vcard):
    jabber_id_full = jabber_id.full if isinstance(jabber_id, sleekxmpp.jid.JID) else jabber_id

    # get_payload() returns the xml for the Iq() as a Element object
    payload = vcard.get_payload()
    vcard_xml = payload[0]
    # first_name = vcard_xml.findtext('.//{vcard-temp}FN')
    name = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
    email = vcard_xml.findtext('.//{vcard-temp}USERID')

    user = XMPPUser(jabber_id_full, name, email)

    logger.debug("create_user_object_from_jid_and_vcard - user is '%s'" % (user))
    return user
