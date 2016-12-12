from dateutil import tz
from datetime import datetime
import logging
import sleekxmpp
from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User, ClientUser

logger = logging.getLogger(__name__)


class XMPP(Client):

    @property
    def integration_name(self):
        return 'xmpp'

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.client = None
        self.password = None
        self.bot_name = None
        self.bot_username = None
        self.room_names = None
        self.server = None
        self.chat_server = None
        self.use_ssl = False
        self.port = 5222

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        for item in settings:
            # Switch on the key
            if item[0] == 'jabber_id':
                self.bot_username = item[1]
            elif item[0] == 'password':
                self.password = item[1]
            elif item[0] == 'room_names':
                self.room_names = item[1].strip().split(',')
            elif item[0] == 'nickname':
                self.bot_name = item[1]
            elif item[0] == 'server':
                self.server = item[1]
            elif item[0] == 'chat_server':
                self.chat_server = item[1]
            elif item[0] == 'use_ssl':
                if item[1] == 'True':
                    self.use_ssl = True
                elif item[1] == 'False':
                    self.use_ssl = False
            elif item[0] == 'port':
                self.port = item[1]

        # Return true if this integrations has the information required to connect
        if self.bot_username is not None and self.password is not None and self.room_names is not None and self.bot_name is not None and self.server is not None and self.chat_server is not None:
            # Make sure there is at least one valid looking room to join (ex. room_names = ,,,,,, should fail)
            if len([x for x in self.room_names if x]) > 0:
                return True
            else:
                logger.error('You must provide at least one chat room in settings.ini for this configuration')
                return False
        else:
            logger.error('XMPP configuration is not valid. Check your settings and try again')
            return False

    def connect(self):
        if self.bot_username is None:
            logger.error('A XMPP username must be configured')
        if self.password is None:
            logger.error('A XMPP password must be configured')

        self.client = MUCBot(self, self.havocbot, self.bot_username, self.password, self.room_names, self.server, self.bot_name, self.chat_server)

        self.client.register_plugin('xep_0030')  # Service Discovery
        self.client.register_plugin('xep_0045')  # Multi-User Chat
        self.client.register_plugin('xep_0054')  # vCard
        self.client.register_plugin('xep_0199', {'keepalive': True, 'interval': 60})  # keep alive ping every 60 seconds

        if self.client.connect(address=(self.server, self.port), use_ssl=self.use_ssl):
            logger.info("I am.. %s! (%s)" % (self.bot_name, self.bot_username))
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
                    self.havocbot.handle_message(self, message_object)
                else:
                    logger.debug("Ignoring non message event of type '%s'" % (message_object.event))

    def send_message(self, text, channel, event=None, **kwargs):
        if channel and text and event:
            logger.info("Sending %s text '%s' to channel '%s'" % (event, text, channel))
            try:
                self.client.send_message(mto=channel, mbody=text, mtype=event)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, text_list, channel, event=None, **kwargs):
        if channel and text_list and event:
            joined_message = '\n'.join(text_list)
            logger.info("Sending %s text list '%s' to channel '%s'" % (event, joined_message, channel))
            try:
                self.client.send_message(mto=channel, mbody=joined_message, mtype=event)
            except AttributeError:
                logger.error('Unable to send message. Are you connected?')
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_user_from_message(self, message_sender, channel=None, event=None, **kwargs):
        user = User(0)

        logger.info("Channel is '%s', message_sender is '%s', event is '%s'" % (channel, message_sender, event))

        # Get client object information
        client_user = self.get_client_object_from_message_object(message_sender, channel=channel, event=event)
        user.client_user = client_user

        user.name = client_user.name
        user.current_username = client_user.username

        return user

    def get_users_in_channel(self, channel, event=None, **kwargs):
        result_list = []

        logger.info('starting get_active_users_in_channel')
        if event is not None and event == 'groupchat':
            roster = self.client.plugin['xep_0045'].getRoster(channel)
            if roster is not None and roster:
                logger.info("roster is '%s'" % (roster))
                for roster_item in roster:
                    logger.info("roster_item is '%s'" % (roster_item))
                    user = self._get_user_from_groupchat(roster_item, channel)
                    if user is not None and user:
                        result_list.append(user)

        return result_list

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

    def _get_user_from_jid(self, jabber_id):
        user = None

        if jabber_id is not None and jabber_id:
            vcard = self._get_vcard_by_jabber_id(jabber_id)
            user = create_user_object_2(jabber_id, vcard)
            # user = self.get_client_object_from_message_object(message_sender, channel=channel, event=event)

            logger.info('Displaying user')
            logger.info(user)
        else:
            logger.info('else clause top')

        return user

    # Uncommented this. Not sure why it was commented out
    def _get_user_from_groupchat(self, name, channel):
        user = None

        # Fetch JID from xep_0045
        if channel is not None and channel:
            if '@' not in channel:
                channel = "%s@%s" % (channel, self.server)

            jabber_id = self.client.plugin['xep_0045'].getJidProperty(channel, name, 'jid')

            if jabber_id is not None and jabber_id.bare is not None and jabber_id.bare:
                vcard = self._get_vcard_by_jabber_id(jabber_id)
                logger.info('Creating user')
                logger.info("jabber_id is '%s', name is '%s' and vcard is '%s'" % (jabber_id, name, vcard))
                user = create_user_object(jabber_id, name, vcard)

                logger.info('Displaying user')
                logger.info(user)
            else:
                logger.info('else clause top')
        else:
            logger.info('else clause')

        return user

    # def _get_user_from_private_chat(self, name):
    #     user = None

    #     if name is not None:
    #         if isinstance(name, sleekxmpp.jid.JID):
    #             jabber_id = name.bare
    #         else:
    #             jabber_id = name

    #         vcard = self._get_vcard_by_jabber_id(jabber_id)
    #         user = create_user_object(jabber_id, name, vcard)

    #         logger.info('_get_user_from_private_chat() - Displaying user')
    #         logger.info(repr(user))

    #     return user

    def _get_vcard_by_jabber_id(self, jabber_id):
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

    def update_user_object_from_message(self, user_object, message_object):
        logger.debug('update_user_object_from_message() - triggered')

        # Get client object information
        client_object = self.get_client_object_from_message_object(message_object.sender, channel=message_object.to, event=message_object.event)

        # user_object.add_client(client_object)
        if client_object is not None:
            if client_object.username is not None:
                user_object.current_username = client_object.username
            if client_object.name is not None:
                user_object.name = client_object.name

    def get_client_object_from_message_object(self, message_sender, channel=None, event=None, **kwargs):
        user = None

        if event is not None and event:
            if event in ['chat', 'normal']:
                user = self._get_client_object_from_private_chat(message_sender)

            elif event in ['groupchat']:
                user = self._get_user_from_jid(message_sender)
                # user = self._get_client_object_from_groupchat(message_sender, channel)

        return user

    def _get_client_object_from_groupchat(self, name, channel):
        user = None

        # Fetch JID from xep_0045
        if channel is not None and channel:
            if '@' not in channel:
                channel = "%s@%s" % (channel, self.server)

            jabber_id = self.client.plugin['xep_0045'].getJidProperty(channel, name, 'jid')

            if jabber_id is not None and jabber_id.bare is not None and jabber_id.bare:
                vcard = self._get_vcard_by_jabber_id(jabber_id)
                user = self.create_client_object_object(jabber_id, name, vcard)

        return user

    def _get_client_object_from_private_chat(self, message_sender):
        user = None

        if message_sender is not None:
            if isinstance(message_sender, sleekxmpp.jid.JID):
                jabber_id = message_sender.bare
            else:
                jabber_id = message_sender

            vcard = self._get_vcard_by_jabber_id(jabber_id)
            user = self.create_client_object_object(jabber_id, message_sender, vcard)

        return user

    def create_client_object_object(self, jabber_id, name, vcard):
        jabber_id_bare = jabber_id.bare if isinstance(jabber_id, sleekxmpp.jid.JID) and jabber_id.bare is not None and jabber_id.bare else jabber_id

        vcard_nickname = None
        vcard_email = None

        if vcard is not None:
            # get_payload() returns the xml for the Iq() as a Element object
            payload = vcard.get_payload()
            vcard_xml = payload[0]
            # vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
            vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
            vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

        client_user = XMPPUser(jabber_id_bare, vcard_nickname if vcard_nickname is not None and vcard_nickname else name, vcard_email if vcard_email is not None and vcard_email else None)
        logger.debug("returning with '%s'" % (client_user))

        return client_user


class MUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, client, havocbot, jid, password, rooms_list, server_host, nick, chat_server):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.havocbot = havocbot
        self.parent = client
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
                message_object = Message(msg['body'], msg['mucnick'], msg['mucroom'], msg['type'], 'xmpp', datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)
        elif msg['type'] in ('normal', 'chat'):
            if msg['from'].bare != self.boundjid.bare:
                message_object = Message(msg['body'], msg['from'], msg['to'], msg['type'], self.parent.integration_name, datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)


class XMPPUser(ClientUser):
    def __init__(self, username, name, email):
        super(XMPPUser, self).__init__(username, 'xmpp')
        self.name = name
        self.email = email

    def __str__(self):
        return "XMPPUser(Username: '%s', Name: '%s', Email: '%s')" % (self.username, self.name, self.email)

    def to_json(self):
        json_data = {
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'client': self.client
        }

        return json_data


# Returns a newly created user from a json source
def create_user_object(jabber_id, name, vcard):
    jabber_id_bare = jabber_id.bare if isinstance(jabber_id, sleekxmpp.jid.JID) and jabber_id.bare is not None and jabber_id.bare else jabber_id

    vcard_nickname = None
    vcard_email = None

    if vcard is not None:
        # get_payload() returns the xml for the Iq() as a Element object
        payload = vcard.get_payload()
        vcard_xml = payload[0]
        # vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
        vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
        vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

    client_user = XMPPUser(jabber_id_bare, vcard_nickname if vcard_nickname is not None and vcard_nickname else name, vcard_email if vcard_email is not None and vcard_email else None)

    # Create a User object
    user_object = User(0)
    user_object.name = name
    user_object.points = 0
    json_data = client_user.to_json()
    user_object.usernames = {json_data['client']: [json_data['username']]}
    user_object.current_username = json_data['username']

    logger.debug("client_user is '%s'" % (client_user))
    return client_user


def create_user_object_2(jabber_id, vcard):
    vcard_nickname = None
    vcard_email = None

    if vcard is not None:
        # get_payload() returns the xml for the Iq() as a Element object
        payload = vcard.get_payload()
        vcard_xml = payload[0]
        vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
        vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
        vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

    client_user = XMPPUser(jabber_id, vcard_nickname if vcard_nickname is not None and vcard_nickname else None, vcard_email if vcard_email is not None and vcard_email else None)

    # # Create a User object
    # user_object = User(0)
    # user_object.points = 0
    # json_data = client_user.to_json()
    # user_object.usernames = {json_data['client']: [json_data['username']]}
    # user_object.current_username = json_data['username']

    logger.debug("client_user is '%s'" % (client_user))
    return client_user

