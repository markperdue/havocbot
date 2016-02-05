from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import json
import logging
import re
from slackclient import SlackClient
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PROCESS_ONE_WORD_TRIGGERS_IF_ONLY_CONTENT_IN_MESSAGE = True


class Slack(Client):
    def __init__(self, havocbot):
        logger.log(0, "__init__ triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).__init__(havocbot)

        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.name = 'slack'
        self.token = None
        self.username = None
        self.user_id = None

        # Do any custom __init__() work here

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        logger.log(0, "configure triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).configure(settings)

        requirements_met = False

        for item in settings:
            # Switch on the key
            if item[0] == 'api_token':
                self.token = item[1]
                requirements_met = True
            elif item[0] == 'admins':
                pass

        # Return true if this integrations has the information required to connect
        if requirements_met:
            return True
        else:
            logger.error("Slack configuration is not valid. Check your settings and try again")
            return False

    def connect(self):
        logger.log(0, "connect triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).connect()

        if not self.token:
            logger.error("A Slack api token must be configured. Get one at https://slack.com/integrations")
            return False

        # logger.debug("Connecting to Slack...")
        self.client = SlackClient(self.token)

        if self.client.rtm_connect():
            return True
        else:
            return False

    def disconnect(self):
        logger.log(0, "disconnect triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).disconnect()

        self.client = None

    def shutdown(self):
        logger.log(0, "shutdown triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).shutdown()

    def process(self):
        logger.log(0, "process triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).process()

        # Set some values from the login_data response
        self.username = self.client.server.login_data["self"]["name"]
        self.user_id = self.client.server.login_data["self"]["id"]

        logger.info("I am.. %s! (%s)" % (self.username, self.user_id))

        while True and self.client is not None:
            try:
                for event in self.client.rtm_read():
                    if 'type' in event:
                        if event['type'] == 'message':
                            logger.debug("raw message received - '%s'" % (event))

                            # Ignore messages originating from havocbot
                            if 'user' in event and event['user'] != self.user_id:
                                message_object = create_message_object_from_json(event)

                                self.handle_message(message_object=message_object)
                        elif event['type'] == 'user_typing':
                            logger.debug("user_typing received - '%s'" % (event))
                        elif event['type'] == 'hello':
                            logger.debug("hello received - '%s'" % (event))
                        elif event['type'] == 'presence_change':
                            logger.debug("presence_change received - '%s'" % (event))
                        elif event['type'] == 'status_change':
                            logger.debug("status_change received - '%s'" % (event))
                        elif event['type'] == 'reconnect_url':
                            logger.debug("reconnect_url received - '%s'" % (event))
                        else:
                            logger.debug("UNKNOWN EVENT received - '%s'" % (event))
                    elif 'reply_to' in event:
                        logger.debug("reply_to received - '%s'" % (event))
                    else:
                        logger.debug("UNKNOWN THING received - '%s'" % (event))
                time.sleep(1)
            except (AttributeError):
                logger.error("We have a problem! Is there a client?")
                break

    def handle_message(self, **kwargs):
        logger.log(0, "handle_message triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).handle_message(**kwargs)

        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.type_ == 'message':
                for trigger, triggered_function in self.havocbot.triggers.items():
                    # Add exact regex match if user defined
                    if len(trigger.split()) == 1 and PROCESS_ONE_WORD_TRIGGERS_IF_ONLY_CONTENT_IN_MESSAGE is True:
                        if not trigger.startswith('^') and not trigger.endswith('$'):
                            # logger.debug("Converting trigger to a line exact match requirement")
                            trigger = "^" + trigger + "$"

                    # logger.debug("trigger is '%s'" % (trigger))
                    # Use trigger as regex pattern and then search the message for a match
                    regex = re.compile(trigger)

                    match = regex.search(message_object.text)
                    if match is not None:
                        # logger.debug("Y MATCH FOR TRIGGER '%s' WITH %s'" % (trigger, match))
                        # Pass the message to the function associated with the trigger
                        triggered_function(self, message_object, capture_groups=match.groups())
                        break
                    else:
                        # logger.debug("N MATCH FOR TRIGGER '%s' WITH %s'" % (trigger, match))
                        pass
            else:
                logger.debug("Ignoring non message event of type '%s'" % (message_object.type_))

    def send_message(self, **kwargs):
        logger.log(0, "send_message triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).send_message(**kwargs)

        if kwargs is not None:
            if 'message' in kwargs and kwargs.get('message') is not None:
                message = kwargs.get('message')
            if 'channel' in kwargs and kwargs.get('channel') is not None:
                channel = kwargs.get('channel')

            if channel and message:
                logger.info("Sending message '%s' to channel '%s'" % (message, channel))
                try:
                    self.client.rtm_send_message(channel, message)
                except AttributeError:
                    logger.error("Unable to send message. Are you connected?")
                except Exception as e:
                    logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, **kwargs):
        logger.log(0, "send_message triggered")

        #  Call super() to pick up any customizations
        # super(self.__class__, self).send_message_from_list(**kwargs)

        if kwargs is not None:
            if 'message' in kwargs and kwargs.get('message') is not None:
                message = kwargs.get('message')
            if 'channel' in kwargs and kwargs.get('channel') is not None:
                channel = kwargs.get('channel')

            if channel and message:
                joined_message = "\n".join(message)
                # logger.info("Sending message list '%s' to channel '%s'" % (joined_message, channel))
                try:
                    self.client.rtm_send_message(channel, joined_message)
                except AttributeError:
                    logger.error("Unable to send message. Are you connected?")
                except Exception as e:
                    logger.error("Unable to send message. %s" % (e))

    def get_user_by_id(self, user_id):
        user = None

        if self.client:
            user_json = self.client.api_call("users.info", user=user_id)
            data = json.loads(user_json.decode())

            user = create_user_object_from_json(data)
        else:
            logger.error("Unable to connect to the slack client")

        if user:
            return user
        else:
            return None
            # raise RuntimeError("No user found for user_id '%s'" % (user_id))


class SlackMessage(Message):
    def __init__(self, text, user, channel, type_, team, reply_to, ts):
        logger.log(0, "__init__ triggered")

        #  Call super() to pick up any customizations with the default initializers
        super(self.__class__, self).__init__(text, user, channel, type_)

        self.team = team
        self.reply_to = reply_to
        self.ts = ts

    def __str__(self):
        return "SlackMessage(Text: '%s', User: '%s', Channel: '%s', Type: '%s', Team: '%s', Reply To: '%s', Timestamp: '%s')" % (self.text, self.user, self.channel, self.type_, self.team, self.reply_to, self.ts)


class SlackUser(User):
    def __init__(self, id, name, real_name, tz):
        logger.log(0, "__init__ triggered")

        #  Call super() to pick up any customizations
        super(self.__class__, self).__init__(real_name, name)

        self.id = id
        self.name = real_name
        self.username = name
        self.tz = tz

    def __str__(self):
        return "SlackUser(Name: '%s', Username: '%s', ID: '%s', Timezone: '%s')" % (self.name, self.username, self.id, self.tz)


def create_message_object_from_json(json):
    text = json['text'] if 'text' in json else None
    user = json['user'] if 'user' in json else None
    channel = json['channel'] if 'channel' in json else None
    type_ = json['type'] if 'type' in json else None
    team = json['team'] if 'team' in json else None
    reply_to = json['reply_to'] if 'reply_to' in json else None
    ts = json['ts'] if 'ts' in json else None

    message = SlackMessage(text, user, channel, type_, team, reply_to, ts)
    logger.debug(message)

    return message


# Returns a newly created user from a json source
def create_user_object_from_json(json):
    logger.debug(json)
    if 'real_name' in json['user'] and len(json['user']['real_name']) > 0:
        real_name = json['user']['real_name']
    else:
        real_name = None

    user = SlackUser(json['user']['id'], json['user']['name'], real_name, json['user']['tz'])
    logger.debug(user)

    return user
