from dateutil import tz
from datetime import datetime
import json
import logging
import requests
import sleekxmpp
from sleekxmpp.xmlstream.stanzabase import ElementBase
from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User, ClientUser

logger = logging.getLogger(__name__)


class HipChat(Client):

    @property
    def integration_name(self):
        return 'hipchat'

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
        self.api_root_url = None
        self.api_token = None

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
            elif item[0] == 'api_root_url':
                self.api_root_url = item[1]
            elif item[0] == 'send_notification_token':
                self.api_token = item[1]

        # Return true if this integrations has the information required to connect
        if self.bot_username is not None and self.password is not None and self.room_names is not None and self.bot_name is not None and self.server is not None and self.chat_server is not None:
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
        if self.bot_username is None:
            logger.error('A XMPP username must be configured')
        if self.password is None:
            logger.error('A XMPP password must be configured')

        self.client = HipMUCBot(self, self.havocbot, self.bot_username, self.password, self.room_names, self.server, self.bot_name, self.chat_server)

        self.client.register_plugin('xep_0030')  # Service Discovery
        self.client.register_plugin('xep_0045')  # Multi-User Chat
        self.client.register_plugin('xep_0054')  # vCard
        self.client.register_plugin('xep_0199', {'keepalive': True, 'interval': 60})  # XMPP Ping set for a keepalive ping every 60 seconds

        if self.client.connect(address=(self.server, 5223), use_ssl=True):
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

    def send_message_api_2(self, url, json_dict):
        logger.debug("POSTING to '%s' with '%s'" % (url, json_dict))
        requests.post(url, json=json_dict, verify=False)

    def send_message_api(self, api_root_url, api_room_id, api_token, json_dict):
        if api_room_id is not None:
            url = '%s/v2/room/%s/notification?auth_token=%s' % (api_root_url, api_room_id, api_token)

            self.send_message_api_2(url, json_dict)
        else:
            logger.info("Unable to get an api room id from a jabber room id")

    def send_message_xmpp(self, message, channel):
        new_test = X()
        new_test.setBasics('system', '0', 'purple', 'text')

        new_test.setNotificationSender('user', '1_422@chat.btf.hipchat.com')
        logger.info(new_test.getNotificationSender())

        json_obj = {}
        json_obj['style'] = 'application'
        json_obj['id'] = 'c253adc6-11fa-4941-ae26-7180d67e814a'
        json_obj['title'] = 'Test'
        json_obj['validation'] = {}
        json_obj['validation']['safehtmls'] = ['activity.html']
        json_obj['validation']['safeurls'] = ['url', 'images.image', 'images.image-small', 'images.image-big', 'icon.url', 'icon.url@2x', 'icon', 'thumbnail.url@2x', 'thumbnail.url']

        new_test.setCard(json.dumps(json_obj))
        logger.info(new_test.getCard())

        # logger.info(dir(new_test))
        # logger.info("Appending XML")
        # message.append(new_test)
        # logger.info(message._get_stanza_values())
        # logger.info(message.values)
        # logger.info(message['x']['color'])
        # logger.info(message.get_payload())
        message.reply('Test').set_payload([new_test.xml])
        message['to'] = channel

    def send_message(self, text, channel, event=None, **kwargs):
        if channel and text and event:
            try:
                used_notification_api = False

                if kwargs is not None:
                    if 'room_id' in kwargs and kwargs.get('room_id') is not None:
                        api_room_id = kwargs.get('room_id')

                        if 'json' in kwargs and kwargs.get('json') is not None:
                            json_dict = kwargs.get('json')
                            logger.info("Found room_id which is '%s' and json which is '%s'" % (api_room_id, json_dict))

                            self.send_message_api(self.api_root_url, api_room_id, self.api_token, json_dict)
                            used_notification_api = True

                if not used_notification_api:
                    logger.info("Sending %s text '%s' to channel '%s'" % (event, text, channel))
                    self.client.send_message(mto=channel, mbody=text, mtype=event)

                    # This was a test to try to send cards over xmpp but the required stanzas to send
                    # to the server are not documented
                    # message = self.client.make_message(mto=channel, mbody=text, mtype=event)
                    # message.send()
                    # self.send_message_xmpp(message, channel)
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

            logger.info('_get_user_from_jid() - Displaying user')
            logger.info(user)
        else:
            logger.info('_get_user_from_jid() - else clause top')

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
                logger.info('_get_user_from_groupchat() - Creating user')
                logger.info("_get_user_from_groupchat() - jabber_id is '%s', name is '%s' and vcard is '%s'" % (jabber_id, name, vcard))
                user = create_user_object(jabber_id, name, vcard)

                logger.info('_get_user_from_groupchat() - Displaying user')
                logger.info(user)
            else:
                logger.info('_get_user_from_groupchat() - else clause top')
        else:
            logger.info('_get_user_from_groupchat() - else clause')

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

        if vcard is not None:
            # get_payload() returns the xml for the Iq() as a Element object
            payload = vcard.get_payload()
            vcard_xml = payload[0]
            # vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
            vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
            vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

        client_user = HipChatUser(jabber_id_bare, vcard_nickname if vcard_nickname is not None and vcard_nickname else name, vcard_email if vcard_email is not None and vcard_email else None)
        logger.debug("create_client_object_object() - returning with '%s'" % (client_user))

        return client_user


class Card(ElementBase):
    namespace = 'http://hipchat.com/protocol/muc#room'
    name = 'card'
    plugin_attrib = 'card'
    interfaces = set(('raw',))
    sub_interfaces = interfaces


class NotificationSender(ElementBase):
    namespace = 'http://hipchat.com/protocol/muc#room'
    name = 'notification_sender'
    plugin_attrib = 'notification_sender'
    interfaces = set(('type', 'id',))
    # sub_interfaces = interfaces


class X(ElementBase):
    namespace = 'http://hipchat.com/protocol/muc#room'
    name = 'x'
    plugin_attrib = 'x'
    interfaces = set(('type', 'notify', 'color', 'message_format', 'card', 'notification_sender'))
    sub_interfaces = set(('type', 'notify', 'color', 'message_format', 'card', 'notification_sender'))
    subitem = (Card, NotificationSender,)

    def setBasics(self, basic_type, notify, color, message_format):
        logger.info("setting basics to '%s', '%s', '%s', and '%s'" % (basic_type, notify, color, message_format))

        self['type'] = basic_type
        self['notify'] = notify
        self['color'] = color
        self['message_format'] = message_format

    def getCard(self):
        raw = ''

        result = self.xml.find('{%s}card' % Card.namespace)
        if result:
            card = Card(result)
            raw = card['raw']

        logger.info("returning with '%s'" % (raw))
        return raw

    def getNotificationSender(self):
        logger.info("getting notification sender...")
        results = {}

        result = self.xml.find('{%s}notification_sender' % NotificationSender.namespace)
        if result:
            logger.info("GOT A RESULT OF '%s'" % (notification_sender['type']))
            logger.info("GOT A RESULT OF '%s'" % (notification_sender['id']))
            notification_sender = NotificationSender(result)
            results['type'] = notification_sender['type']
            results['id'] = notification_sender['id']

        logger.info("returning with '%s'" % (results))
        return results

    def setCard(self, json_string):
        logger.info("setting card to '%s'" % (json_string))

        card_obj = Card(None, self)
        card_obj['raw'] = json_string

    def setNotificationSender(self, sender_type, sender_id):
        logger.info("setting notification_sender to '%s' and '%s'" % (sender_type, sender_id))

        notification_sender = NotificationSender(None, self)
        notification_sender['type'] = sender_type
        notification_sender['id'] = sender_id


class HipMUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, client, havocbot, jid, password, rooms_list, server_host, nick, chat_server):
        sleekxmpp.ClientXMPP.__init__(self, jid + '/bot', password)

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
                from_jid = msg._get_attr('from_jid')

                if from_jid is not None and from_jid:
                    msg_from = from_jid
                else:
                    jabber_id = self.plugin['xep_0045'].getJidProperty(msg['mucroom'], msg['mucnick'], 'jid')

                    if jabber_id is not None:
                        msg_from = jabber_id.bare
                    else:
                        msg_from = msg['mucnick']

                message_object = Message(msg['body'], msg_from, msg['mucroom'], msg['type'], self.parent.integration_name, datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)
                    raise

        elif msg['type'] in ('normal', 'chat'):
            if msg['from'].bare != self.boundjid.bare:
                message_object = Message(msg['body'], msg['from'].bare, msg['to'].bare, msg['type'], self.parent.integration_name, datetime.utcnow().replace(tzinfo=tz.tzutc()))
                logger.info("Processed %s - %s" % (msg['type'], message_object))

                try:
                    self.parent.handle_message(message_object=message_object)
                except Exception as e:
                    logger.error(e)


class HipChatUser(ClientUser):
    def __init__(self, username, name, email):
        super(HipChatUser, self).__init__(username, 'hipchat')
        self.name = name
        self.email = email

    def __str__(self):
        return "HipChatUser(Username: '%s', Name: '%s', Email: '%s')" % (self.username, self.name, self.email)

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

    if vcard is not None:
        # get_payload() returns the xml for the Iq() as a Element object
        payload = vcard.get_payload()
        vcard_xml = payload[0]
        # vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
        vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
        vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

    client_user = HipChatUser(jabber_id_bare, vcard_nickname if vcard_nickname is not None and vcard_nickname else name, vcard_email if vcard_email is not None and vcard_email else None)

    # Create a User object
    user_object = User(0)
    user_object.name = name
    user_object.points = 0
    json_data = client_user.to_json()
    user_object.usernames = {json_data['client']: [json_data['username']]}
    user_object.current_username = json_data['username']

    logger.debug("create_user_object - client_user is '%s'" % (client_user))
    return client_user


def create_user_object_2(jabber_id, vcard):
    if vcard is not None:
        # get_payload() returns the xml for the Iq() as a Element object
        payload = vcard.get_payload()
        vcard_xml = payload[0]
        vcard_full_name = vcard_xml.findtext('.//{vcard-temp}FN')
        vcard_nickname = vcard_xml.findtext('.//{vcard-temp}NICKNAME')
        vcard_email = vcard_xml.findtext('.//{vcard-temp}USERID')

    client_user = HipChatUser(jabber_id, vcard_nickname if vcard_nickname is not None and vcard_nickname else None, vcard_email if vcard_email is not None and vcard_email else None)

    # # Create a User object
    # user_object = User(0)
    # user_object.points = 0
    # json_data = client_user.to_json()
    # user_object.usernames = {json_data['client']: [json_data['username']]}
    # user_object.current_username = json_data['username']

    logger.debug("create_user_object - client_user is '%s'" % (client_user))
    return client_user

