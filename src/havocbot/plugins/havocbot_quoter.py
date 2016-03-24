#!/havocbot

from dateutil import tz, parser
from datetime import datetime
from havocbot.plugin import HavocBotPlugin
from havocbot.stasher import Stasher
import havocbot.user
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
            ("!quote <name>", "!quote markaperdue", "get a quote said by a user"),
            ("!addquote <name>", "!addquote markaperdue", "add the last message said by the user to the database"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!quote\s(.*)", self.get_quote),
            ("!addquote\s(.*)", self.add_quote),
            ("!debugquote", self.debug_quote),
            ("!quotes", self.get_quotes),
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
        captured_name = capture[0]

        if message.to and captured_name is not None:
            for (message_sender, message_text, integration_name, message_to, timestamp) in self.recent_messages:
                if captured_name == message_sender:
                    text = "%s said '%s' on '%s' in '%s' on client '%s'" % (message_sender, message_text, str(timestamp), message_to, integration_name)
                    callback.send_message(text, message.to, event=message.event)

    def quote_as_string(self, quote_dict, user_object=None):
        result = None

        if quote_dict is not None and 'user_id' in quote_dict and 'quote' in quote_dict:
            if user_object is not None and user_object and user_object.name is not None and len(user_object.name) > 0:
                name = user_object.name
            else:
                name = quote_dict['user_id']

            if 'timestamp' in quote_dict:
                date = parser.parse(quote_dict['timestamp'])
                result = "%s said '%s' on %s" % (name, quote_dict['quote'], format_datetime_for_display(date))
            else:
                result = "%s said '%s'" % (name, quote_dict['quote'])

        return result

    def get_quote(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_names = capture[0]
        words = captured_names.split()

        if len(words) <= 5:
            stasher = StasherQuote.getInstance()
            stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')
            # logger.debug("stasher_data is '%s'" % (stasher.plugin_data))

            temp_list = []
            for word in words:
                is_quote_found_for_user = False
                user = havocbot.user.find_user_by_id_or_name(word, message.client, callback)
                if user is not None and user:
                    quote = stasher.get_quote_from_user_id(user.user_id)
                    if quote is not None:
                        display_quote = self.quote_as_string(quote, user)
                        temp_list.append(display_quote)
                        is_quote_found_for_user = True

                if not is_quote_found_for_user:
                    temp_list.append("No quotes found from user %s" % (word))

            callback.send_messages_from_list(temp_list, message.to, event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            callback.send_message(text, message.to, event=message.event)

    def get_quotes(self, callback, message, **kwargs):
        stasher = StasherQuote.getInstance()
        stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')
        # logger.debug("stasher_data is '%s'" % (stasher.plugin_data))

        message_list = []
        quotes = stasher.get_quotes()
        if quotes is not None and quotes:
            message_list.append("There are %d known quotes" % (len(quotes)))
            for quote in quotes:
                display_quote = self.quote_as_string(quote)
                if display_quote is not None:
                    message_list.append(display_quote)
        else:
            message_list.append("There are no known quote")

        callback.send_messages_from_list(message_list, message.to, event=message.event)

    def search_messages_for_user_match(self, message_list, user_object, reverse=None):
        if reverse is True:
            message_list = message_list[::-1]
            # message_list = list(reversed(message_list))  # Another approach

        for message in message_list:
            if message[0].lower() == user_object.user_id.lower():
                return message
            elif message[0].lower() == user_object.name.lower():
                return message
            elif message[0].lower() == user_object.username.lower():
                return message
            elif user_object.aliases is not None and user_object.aliases and message[0].lower() in user_object.aliases.lower():
                return message

        return None

    def add_quote(self, callback, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_name = capture[0]

        stasher = StasherQuote.getInstance()
        stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')

        user = havocbot.user.find_user_by_id_or_name(captured_name, message.client, callback)
        if user is not None and user and user.is_valid() is True:
            # !addquote bossman
            found_message = self.search_messages_for_user_match(self.recent_messages, user, reverse=True)
            logger.info("found_message is '%s'" % (str(found_message)))

            if found_message is not None and found_message:
                stasher.add_quote(user.user_id, found_message[1], found_message[2], found_message[3], found_message[4])
                text = "%s said something ridiculous. Archived it" % (user.name)
                callback.send_message(text, message.to, event=message.event)
            else:
                text = "No recent messages found from %s" % (user.name)
                callback.send_message(text, message.to, event=message.event)
        else:
            text = "Unable to find a user matching %s" % (captured_name)
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

        self.plugin_data = self.get_plugin_data('havocbot_quoter')
        logger.info("stasher_data is '%s'" % (self.plugin_data))

        if self.plugin_data is not None:
            if 'quotes' in self.plugin_data:
                if any((known_quote['user_id'] == user_id and known_quote['quote'] == quote) for known_quote in self.plugin_data['quotes']):
                    print("Quote db already contains the quote '%s' for user_id %s" % (quote, user_id))
                else:
                    print("Adding quote")
                    self.plugin_data['quotes'].append({'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp})
                    self.write_plugin_data('havocbot_quoter')
            else:
                print("Adding initial quote")
                self.plugin_data['quotes'] = [{'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
                self.write_plugin_data('havocbot_quoter')
        else:
            self.plugin_data['quotes'] = [{'user_id': user_id, 'quote': quote, 'client': client, 'channel': channel, 'timestamp': timestamp}]
            self.write_plugin_data('havocbot_quoter')

    def get_quote_from_user_id(self, user_id):
        quote = None
        if self.plugin_data is not None:
            if 'quotes' in self.plugin_data:
                results = [x for x in self.plugin_data['quotes'] if x['user_id'] == user_id]
                if results is not None and results:
                    quote = random.choice(results)

        logger.debug("StasherQuote.get_quote_from_user_id() returning with '%s'" % (quote))
        return quote

    def get_quotes(self):
        results = []
        if self.plugin_data is not None:
            if 'quotes' in self.plugin_data:
                for quote in self.plugin_data['quotes']:
                    results.append(quote)

        return results

    def display_quotes(self):
        quotes = self.get_quotes()
        if quotes:
            print("There are %d known quotes" % (len(quotes)))
            for quote in quotes:
                print(quote)
        else:
            print("There are no known quote")


# Make this plugin available to HavocBot
havocbot_handler = QuoterPlugin()
