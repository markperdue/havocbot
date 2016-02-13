from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
import signal
import sleekxmpp
import threading

logger = logging.getLogger(__name__)

PROCESS_ONE_WORD_TRIGGERS_IF_ONLY_CONTENT_IN_MESSAGE = True


class HipChat(Client):

    @property
    def integration_name(self):
        return "hipchat"

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.token = None
        self.username = None
        self.room_name = None
        self.nickname = None
        self.server = None

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
            logger.error("HipChat configuration is not valid. Check your settings and try again")
            return False

    def connect(self):
        if self.username is None:
            logger.error("A XMPP username must be configured")
        if self.password is None:
            logger.error("A XMPP password must be configured")

        self.client = HipMUCBot(self, self.havocbot, self.username, self.password, self.room_name + "@" + self.server, self.nickname)

        # self.client.use_signals(signals=['SIGHUP', 'SIGTERM', 'SIGINT'])

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
            for thread in self.all_threads:
                logger.debug("Stopping thread %s" % (thread))
                thread.running = False
                thread.stop()

    def process(self):
        self.all_threads = []

        signal.signal(signal.SIGINT, self.havocbot.signal_handler)
        a_thread = HipChatThread(self.client)
        a_thread.daemon = True
        self.all_threads.append(a_thread)
        a_thread.start()

    def handle_message(self, **kwargs):
        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.type_ == 'message':
                for (trigger, triggered_function) in self.havocbot.triggers:
                    logger.debug("trigger is '%s', triggered_function is '%s'" % (trigger, str(triggered_function)))

                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and PROCESS_ONE_WORD_TRIGGERS_IF_ONLY_CONTENT_IN_MESSAGE is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            logger.debug("Converting trigger to a line exact match requirement")
                            trigger = "^" + trigger + "$"

                    # Use trigger as regex pattern and then search the message for a match
                    regex = re.compile(trigger)

                    match = regex.search(message_object.text)
                    if match is not None:
                        logger.debug("Y MATCH FOR TRIGGER '%s' WITH %s'" % (trigger, match))

                        logger.info("Received event for trigger '%s'" % (trigger))

                        # Pass the message to the function associated with the trigger
                        try:
                            triggered_function(self, message_object, capture_groups=match.groups())
                        except Exception as e:
                            logger.error(e)

                        break
                    else:
                        logger.debug("N MATCH FOR TRIGGER '%s' WITH %s'" % (trigger, match))
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


class HipMUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, callback, havocbot, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid + "/bot", password)

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
        # logger.info("msg['type'] is '%s', msg['to'] is '%s', msg['from'] is '%s', msg['mucroom'] is '%s', msg['mucnick'] is '%s', " % (msg['type'], msg['to'], msg['from'], msg['mucroom'], msg['mucnick'], ))
        if msg['mucnick'] != self.nick:
            message_object = Message(msg['body'], msg['mucnick'], self.room, "message")

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


class HipChatThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        logger.debug("Running a background thread for %s" % (self.__class__.__name__))
        self.client.process(block=True)

    def stop(self):
        self.client.set_stop()
