import logging
from slackclient import SlackClient
from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User, ClientUser

logger = logging.getLogger(__name__)


class Slack(Client):

    @property
    def integration_name(self):
        return "slack"

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.client = None
        self.token = None
        self.bot_name = None
        self.bot_username = None

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = False

        for item in settings:
            # Switch on the key
            if item[0] == 'api_token':
                self.token = item[1]
                requirements_met = True

        # Return true if this integrations has the information required to connect
        if requirements_met:
            return True
        else:
            logger.error("Slack configuration is not valid. Check your settings and try again")
            return False

    def connect(self):
        if not self.token:
            logger.error("A Slack api token must be configured. Get one at https://slack.com/integrations")
            return False

        self.client = SlackClient(self.token)

        if self.client.rtm_connect():
            # Set some values from the login_data response
            self.bot_name = self.client.server.login_data["self"]["name"]
            self.bot_username = self.client.server.login_data["self"]["id"]

            logger.info("I am.. %s! (%s)" % (self.bot_name, self.bot_username))
            return True
        else:
            return False

    def disconnect(self):
        if self.client is not None:
            self.client.server.websocket.close()
            self.client = None

    def process(self):
        while not self.havocbot.should_shutdown:
            try:
                for event in self.client.rtm_read():
                    if 'type' in event:
                        if event['type'] == 'message':
                            logger.debug("raw message received - '%s'" % (event))

                            # Ignore messages originating from havocbot
                            if 'user' in event and event['user'] != self.bot_username:
                                message_object = create_message_object_from_json(event)
                                logger.info("Received - %s" % (message_object))

                                try:
                                    self.handle_message(message_object=message_object)
                                except Exception as e:
                                    logger.error("Unable to handle the message")
                                    logger.error(e)
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
            except AttributeError as e:
                logger.error("We have a problem! Is there a client?")
                logger.error(e)

    def handle_message(self, **kwargs):
        if kwargs is not None:
            if 'message_object' in kwargs and kwargs.get('message_object') is not None:
                message_object = kwargs.get('message_object')

            if message_object.event == 'message':
                self.havocbot.handle_message(self, message_object)
            else:
                logger.debug("Ignoring non message event of type '%s'" % (message_object.event))

    def send_message(self, text, channel, event=None, **kwargs):
        if channel and text:
            logger.info("Sending text '%s' to '%s'" % (text, channel))
            try:
                self.client.rtm_send_message(channel, text)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, text_list, to, event=None, **kwargs):
        if to and text_list:
            joined_message = "\n".join(text_list)
            logger.info("Sending text list '%s' to '%s'" % (joined_message, to))
            try:
                self.client.rtm_send_message(to, joined_message)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_user_from_message(self, message_sender, channel=None, event=None, **kwargs):
        user = User(0)

        logger.info("Channel is '%s', message_sender is '%s', event is '%s'" % (channel, message_sender, event))

        api_json = self.client.api_call('users.info', user=message_sender)
        if 'user' in api_json and api_json['user'] is not None:
            client_user = create_user_object_from_json(api_json['user'])
            user.client_user = client_user

            user.name = client_user.name
            user.current_username = client_user.username

        return user

    def get_users_in_channel(self, channel, event=None, **kwargs):
        result_list = []

        if self.client:
            result = self.client.api_call('users.list', presence=1)
            if 'members' in result and result['members']:
                for member in result['members']:
                    if 'presence' in member and member['presence'] is not None and member['presence'] == 'active':
                        a_user = create_user_object_from_json(member)
                        result_list.append(a_user)

        return result_list


class SlackMessage(Message):
    def __init__(self, text, sender, to, event, client, team, reply_to, timestamp):
        super(SlackMessage, self).__init__(text, sender, to, event, client, timestamp)
        self.team = team
        self.reply_to = reply_to

    def __str__(self):
        return "SlackMessage(Text: '%s', Sender: '%s', To: '%s', Event: '%s', Team: '%s', Reply To: '%s', Timestamp: '%s')" % (self.text, self.sender, self.to, self.event, self.team, self.reply_to, self.timestamp)

    def reply(self):
        return self.to


class SlackUser(ClientUser):
    def __init__(self, username, name):
        super(SlackUser, self).__init__(username, 'slack')
        self.name = name
        self.real_name = None
        self.first_name = None
        self.tz = None

    def __str__(self):
        return "SlackUser(Username: '%s', Name: '%s', Real Name: '%s', Timezone: '%s')" % (self.username, self.name, self.real_name, self.tz)


def create_message_object_from_json(json_data):
    logger.debug(json_data)

    text = json_data['text'] if 'text' in json_data else None
    sender = json_data['user'] if 'user' in json_data else None
    to = json_data['channel'] if 'channel' in json_data else None
    event = json_data['type'] if 'type' in json_data else None
    team = json_data['team'] if 'team' in json_data else None
    reply_to = json_data['reply_to'] if 'reply_to' in json_data else None
    timestamp = json_data['ts'] if 'ts' in json_data else None

    message = SlackMessage(text, sender, to, event, 'slack', team, reply_to, timestamp)

    return message


def create_user_object_from_json(json_user_data):
    logger.debug(json_user_data)

    username = json_user_data['id'] if 'id' in json_user_data and json_user_data['id'] is not None and len(json_user_data['id']) > 0 else None
    name = json_user_data['name'] if 'name' in json_user_data and json_user_data['name'] is not None and len(json_user_data['name']) > 0 else None
    real_name = json_user_data['real_name'] if 'real_name' in json_user_data and json_user_data['real_name'] is not None and len(json_user_data['real_name']) > 0 else None
    first_name = json_user_data['first_name'] if 'first_name' in json_user_data and json_user_data['first_name'] is not None and len(json_user_data['first_name']) > 0 else None
    time_zone = json_user_data['tz'] if 'tz' in json_user_data and json_user_data['tz'] is not None and len(json_user_data['tz']) > 0 else None

    user = SlackUser(username, name)
    user.real_name = real_name
    user.first_name = first_name
    user.tz = time_zone

    return user
