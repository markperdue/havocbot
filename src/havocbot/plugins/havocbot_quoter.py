#!/havocbot

from dateutil import tz, parser
from datetime import datetime
from havocbot.plugin import HavocBotPlugin
from havocbot.stasher import Stasher
import logging
import random

logger = logging.getLogger(__name__)


class QuoterPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "quote management"

    @property
    def plugin_short_name(self):
        return "quoter"

    @property
    def plugin_usages(self):
        return [
            ("!quote <username>", "!quote markaperdue", "get a quote said by a user"),
            ("!addquote <username>", "!addquote markaperdue", "add the last message said by the user to the database"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!quote\s(.*)", self.get_quote),
            ("!addquote\s(.*)", self.add_quote),
            ("!debugquote", self.debug_quote),
            ("(.*)", self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.recent_messages = []
        self.max_messages_per_user_per_channel = 5

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        if message.text.startswith(('!addquote', '!debugquote')):
            return

        # message_string = "User: '%s', Channel: '%s', Timestamp: '%s', Text: '%s'" % (message.sender, message.to, message.timestamp, message.text)
        # logger.info(message_string)

        timestamp = datetime.utcnow().replace(tzinfo=tz.tzutc())
        a_message_tuple = (message.sender, message.text, callback.integration_name, message.to, timestamp.isoformat())

        # Count occurences of messages by a user in a client integration
        previous_messages = [x for x in self.recent_messages if x[0] == message.sender and x[2] == callback.integration_name and x[3] == message.to]
        logger.info("tracked messages for user %s in channel %s is %d" % (message.sender, message.to, len(previous_messages)))

        if len(previous_messages) >= self.max_messages_per_user_per_channel:
            # Remove oldest message from this user for the client
            try:
                self.recent_messages.remove(previous_messages[0])
            except ValueError:
                pass

        logger.info("Adding message by user %s to recent messages" % (message.sender))

        # Add new message
        self.recent_messages.append(a_message_tuple)

    def get_recent_messages(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_username = capture[0]

        if message.to and captured_username is not None:
            for (username, client, text, channel, timestamp) in self.recent_messages:
                if captured_username == username:
                    text = "%s said '%s' on '%s' in channel '%s' on client '%s'" % (username, text, str(timestamp), channel, client)
                    callback.send_message(text, message.to, event=message.event)

    def get_quote(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_usernames = capture[0]
        words = captured_usernames.split()

        if len(words) <= 5:
            stasher = StasherQuote.getInstance()
            temp_list = []
            for word in words:
                logger.info("Looking for quotes for '%s'" % (word))
                result = stasher.get_quote_from_username(word)

                if result is not None and 'username' in result and 'quote' in result:
                    if 'timestamp' in result:
                        date = parser.parse(result['timestamp'])
                    temp_list.append("%s said '%s' on %s" % (result['username'], result['quote'], format_datetime_for_display(date)))
                else:
                    temp_list.append("No quotes found from user %s" % (word))
            callback.send_messages_from_list(temp_list, message.to, event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            callback.send_message(text, message.to, event=message.event)

    def add_quote(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_username = capture[0]

        stasher = StasherQuote.getInstance()

        # logger.info("captured_username is '%s', integration_name is '%s', channel is '%s'" % (captured_username, callback.integration_name, message.to))

        if message.to and captured_username is not None:
            found_message = next((
                x for x in reversed(self.recent_messages)
                if x[0].lower() == captured_username.lower()
                and x[2].lower() == callback.integration_name.lower()
                and x[3].lower() == message.to.lower()
            ), None)

            if found_message is not None:
                name = found_message[0]
                logger.info("Searching for user_id for '%s'" % (name))
                # Fetch the user_id of the message
                users = callback.get_users_by_name(name, channel=message.to)
                if users is not None and len(users) == 1:
                    stasher.add_quote(users[0].user_id, found_message[1], found_message[2], found_message[3], found_message[4])
                    text = "%s said something ridiculous. Archiving it" % (captured_username)
                    callback.send_message(text, message.to, event=message.event)
                else:
                    text = "Unable to fetch user id for %s" % (captured_username)
                    callback.send_message(text, message.to, event=message.event)
            else:
                text = "No recent messages found for user %s" % (captured_username)
                callback.send_message(text, message.to, event=message.event)

    def debug_quote(self, callback, message, **kwargs):
        for message in self.recent_messages:
            logger.info(message)


def format_datetime_for_display(date_object):
    # Convert to local timezone from UTC timezone
    return date_object.astimezone(tz.tzlocal()).strftime("%A %B %d %Y %I:%M%p")


class StasherQuote(Stasher):
    def add_quote(self, user_id, quote, client, channel, timestamp):
        logger.info("Adding new quote - user_id '%s', client '%s', channel '%s', timestamp '%s', quote '%s'" % (user_id, client, channel, timestamp, quote))
        if self.data is not None:
            if 'quotes' in self.data:
                if any((known_quote['user_id'] == user_id and known_quote['quote'] == quote) for known_quote in self.data['quotes']):
                    print("Quote db already contains the quote '%s' for user_id %s" % (quote, user_id))
                else:
                    print("Adding quote")
                    self.data['quotes'].append({'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp})
                    self.write_db()
            else:
                print("Adding initial quote")
                self.data['quotes'] = [{'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
                self.write_db()
        else:
            self.data['quotes'] = [{'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
            self.write_db()

    def get_quote_from_username(self, username):
        quote = None
        if self.data is not None:
            if 'quotes' in self.data:
                results = [x for x in self.data['quotes'] if x['username'] == username]
                if results is not None and len(results) > 0:
                    quote = random.choice(results)

        logger.debug("StasherQuote.get_quote_from_username() returning with '%s'" % (quote))
        return quote

    def get_quotes(self):
        results = []
        if self.data is not None:
            if 'quotes' in self.data:
                for quote in self.data['quotes']:
                    results.append(quote)

        return results

    def display_quotes(self):
        quotes = self.get_quotes()
        if len(quotes) > 0:
            print("There are %d known quotes" % (len(quotes)))
            for quote in quotes:
                print(quote)
        else:
            print("There are no known quote")


# Make this plugin available to HavocBot
havocbot_handler = QuoterPlugin()
