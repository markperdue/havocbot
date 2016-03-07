from havocbot.client import Client
from havocbot.message import Message
from havocbot.user import User
import logging
import re
from slackclient import SlackClient

logger = logging.getLogger(__name__)


class Slack(Client):

    @property
    def integration_name(self):
        return "slack"

    def __init__(self, havocbot):
        # Capture a reference to havocbot
        self.havocbot = havocbot

        self.token = None
        self.name = None
        self.user_id = None
        self.exact_match_one_word_triggers = False

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = False

        for item in settings:
            # Switch on the key
            if item[0] == 'api_token':
                self.token = item[1]
                requirements_met = True
            elif item[0] == 'admins':
                pass

        # Set exact_match_one_word_triggers based off of value in havocbot if it is set
        settings_value = self.havocbot.get_havocbot_setting_by_name('exact_match_one_word_triggers')
        if settings_value is not None and settings_value.lower() == 'true':
            self.exact_match_one_word_triggers = True

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
            self.name = self.client.server.login_data["self"]["name"]
            self.user_id = self.client.server.login_data["self"]["id"]

            logger.info("I am.. %s! (%s)" % (self.name, self.user_id))
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
                            if 'user' in event and event['user'] != self.user_id:
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
        if channel and message:
            logger.info("Sending message '%s' to channel '%s'" % (message, channel))
            try:
                self.client.rtm_send_message(channel, message)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def send_messages_from_list(self, message, channel, event, **kwargs):
        if channel and message:
            joined_message = "\n".join(message)
            logger.info("Sending message list '%s' to channel '%s'" % (joined_message, channel))
            try:
                self.client.rtm_send_message(channel, joined_message)
            except AttributeError:
                logger.error("Unable to send message. Are you connected?")
            except Exception as e:
                logger.error("Unable to send message. %s" % (e))

    def get_user_by_id(self, user_id, **kwargs):
        if self.client:
            user_json = self.client.api_call('users.info', user=user_id)
            logger.debug(user_json)

        return create_user_object_from_json(user_json['user']) if user_json is not None and 'user' in user_json else None

    def get_users_by_name(self, name, channel=None, **kwargs):
        results = []

        if self.client:
            api_users = self.get_users_in_channel(None)
            logger.info('api users below')
            logger.info(api_users)
            matched_users = [x for x in api_users if (x.username is not None and x.username.lower() == name.lower()) or (x.name is not None and x.name.lower() == name.lower())]
            if matched_users:
                if len(matched_users) > 1:
                    results = matched_users
                else:
                    results.append(matched_users[0])

        logger.debug("get_users_by_name returning with '%s'" % (results))
        return results

    def get_users_in_channel(self, team, **kwargs):
        result_list = []

        if self.client:
            result = self.client.api_call('users.list', presense=0)
            if 'members' in result and result['members']:
                for member in result['members']:
                    a_user = create_user_object_from_json(member)
                    result_list.append(a_user)

        return result_list


class SlackMessage(Message):
    def __init__(self, text, user, channel, event, team, reply_to, timestamp):
        self.text = text
        self.user = user
        self.channel = channel
        self.event = event
        self.team = team
        self.reply_to = reply_to
        self.timestamp = timestamp

    def __str__(self):
        return "SlackMessage(Text: '%s', User: '%s', Channel: '%s', Type: '%s', Team: '%s', Reply To: '%s', Timestamp: '%s')" % (self.text, self.user, self.channel, self.event, self.team, self.reply_to, self.timestamp)


class SlackUser(User):
    def __init__(self, user_id, name, username, tz):
        super(SlackUser, self).__init__(user_id)
        self.user_id = user_id
        self.name = name
        self.username = username
        self.tz = tz

    def __str__(self):
        return "SlackUser(User ID: '%s', Name: '%s', Username: '%s', Timezone: '%s')" % (self.user_id, self.name, self.username, self.tz)


def create_message_object_from_json(json_data):
    text = json_data['text'] if 'text' in json_data else None
    user = json_data['user'] if 'user' in json_data else None
    channel = json_data['channel'] if 'channel' in json_data else None
    event = json_data['type'] if 'type' in json_data else None
    team = json_data['team'] if 'team' in json_data else None
    reply_to = json_data['reply_to'] if 'reply_to' in json_data else None
    timestamp = json_data['ts'] if 'ts' in json_data else None

    message = SlackMessage(text, user, channel, event, team, reply_to, timestamp)

    return message


def create_user_object_from_json(json_user_data):
    user_id = json_user_data['id'] if 'id' in json_user_data and json_user_data['id'] is not None and len(json_user_data['id']) > 0 else None
    name = json_user_data['real_name'] if 'real_name' in json_user_data and json_user_data['real_name'] is not None and len(json_user_data['real_name']) > 0 else None
    username = json_user_data['name'] if 'name' in json_user_data and json_user_data['name'] is not None and len(json_user_data['name']) > 0 else None
    time_zone = json_user_data['tz'] if 'tz' in json_user_data and json_user_data['tz'] is not None and len(json_user_data['tz']) > 0 else None

    user = SlackUser(user_id, name, username, time_zone)
    user.client = 'slack'

    return user
