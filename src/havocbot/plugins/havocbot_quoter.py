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
        return (
            ("!quote <username>", "!quote markaperdue", "get a quote said by a user"),
            ("!addquote <username>", "!addquote markaperdue", "add the last message said by the user to the database"),
        )

    @property
    def plugin_triggers(self):
        return (
            ("!quote\s(.*)", self.get_quote),
            ("!addquote\s(.*)", self.add_quote),
            ("(.*)", self.start),
        )

    def init(self, havocbot):
        self.havocbot = havocbot
        self.recent_messages = []

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        message_string = "User: '%s', Channel: '%s', Timestamp: '%s', Text: '%s'" % (message.user, message.channel, message.ts, message.text)
        logger.info(callback.get_user_by_id(message.user))
        logger.info(message_string)

        # Remember only the past 5 messages said by a user. Quoter can potentially
        # be running across multiple clients so the recent_messages list has entries
        # setup like the following tuple:
        # (User.username, message.text, Client.integration_name, message.channel, message.ts)
        user = callback.get_user_by_id(message.user)
        if user:
            timestamp = datetime.utcnow().replace(tzinfo=tz.tzutc())
            a_message_tuple = (user.username, message.text, callback.integration_name, message.channel, timestamp.isoformat())
            self.recent_messages.append(a_message_tuple)
        else:
            timestamp = datetime.utcnow().replace(tzinfo=tz.tzutc())
            a_message_tuple = (message.user, message.text, callback.integration_name, message.channel, timestamp.isoformat())
            self.recent_messages.append(a_message_tuple)

    def get_recent_messages(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_username = capture[0]

        if message.channel and captured_username is not None:
            for (username, client, text, channel, timestamp) in self.recent_messages:
                if captured_username == username:
                    text = "%s said '%s' on '%s' in channel '%s' on client '%s'" % (username, text, str(timestamp), channel, client)
                    callback.send_message(channel=message.channel, message=text)

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
            callback.send_messages_from_list(channel=message.channel, message=temp_list)
        else:
            callback.send_message(channel=message.channel, message="Too many parameters. What are you trying to do?")

    def add_quote(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_username = capture[0]

        stasher = StasherQuote.getInstance()

        if message.channel and captured_username is not None:
            for (username, quote, client, channel, timestamp) in reversed(self.recent_messages):
                if username == captured_username:
                    stasher.add_quote(username, quote, client, channel, timestamp)
                    text = "%s said something ridiculous. Archiving it" % (username)
                    callback.send_message(channel=message.channel, message=text)
                    break


def format_datetime_for_display(date_object):
    # Convert to local timezone from UTC timezone
    return date_object.astimezone(tz.tzlocal()).strftime("%A %B %d %Y %I:%M%p")


class StasherQuote(Stasher):
    def add_quote(self, username, quote, client, channel, timestamp):
        if self.data is not None:
            if 'quotes' in self.data:
                if any((known_quote['username'] == username and known_quote['quote'] == quote) for known_quote in self.data['quotes']):
                    print("Quote db already contains the quote '%s' for username %s" % (quote, username))
                else:
                    print("Adding alias")
                    self.data['quotes'].append({'username': username, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp})
                    self.write_db()
            else:
                print("Adding initial quote")
                self.data['quotes'] = [{'username': username, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
                self.write_db()
        else:
            self.data['quotes'] = [{'username': username, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
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
