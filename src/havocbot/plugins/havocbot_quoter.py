#!/havocbot

from dateutil import tz, parser
from datetime import datetime
import logging
import random
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.stasher import Stasher
import havocbot.user

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
            Usage(command="!quote <name>", example="!quote markaperdue", description="get a quote said by a user"),
            Usage(command="!addquote <name>", example="!addquote markaperdue", description="add the last message said by the user to storage"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!quote\s(.*)", function=self.get_quote, param_dict=None, requires=None),
            Trigger(match="!addquote\s(.*)", function=self.add_quote, param_dict=None, requires=None),
            Trigger(match="!debugquote", function=self.debug_quote, param_dict=None, requires=None),
            Trigger(match="!quotes", function=self.get_quotes, param_dict=None, requires=None),
            Trigger(match="(.*)", function=self.start, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.recent_messages = []
        self.max_messages_per_user_per_channel = 5
        self.same_channel_only = False

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'same_channel_only':
                    self.same_channel_only = item[1]

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, client, message, **kwargs):
        if message.text.startswith(('!addquote', '!debugquote')):
            return

        # message_string = "User: '%s', Channel: '%s', Timestamp: '%s', Text: '%s'" % (message.sender, message.to, message.timestamp, message.text)
        # logger.info(message_string)

        timestamp = datetime.utcnow().replace(tzinfo=tz.tzutc())
        a_message_tuple = (message.sender, message.text, message.to, message.event, client.integration_name, timestamp.isoformat())

        # Count occurences of messages by a user in a client integration
        previous_messages = [x for x in self.recent_messages if x[0] == message.sender and x[2] == client.integration_name and x[3] == message.to]
        logger.debug("tracked messages for user %s in channel %s is %d" % (message.sender, message.to, len(previous_messages)))

        if len(previous_messages) >= self.max_messages_per_user_per_channel:
            # Remove oldest message from this user for the client
            try:
                self.recent_messages.remove(previous_messages[0])
            except ValueError:
                pass

        logger.debug("Adding message by user %s to recent messages" % (message.sender))

        # Add new message
        self.recent_messages.append(a_message_tuple)

    def get_recent_messages(self, client, message, **kwargs):
        # Get the results of the capture
        capture = kwargs.get('capture_groups', None)
        captured_name = capture[0]

        if message.to and captured_name is not None:
            for (message_sender, message_text, integration_name, message_to, timestamp) in self.recent_messages:
                if captured_name == message_sender:
                    text = "%s said '%s' on '%s' in '%s' on client '%s'" % (message_sender, message_text, str(timestamp), message_to, integration_name)
                    client.send_message(text, message.reply(), event=message.event)

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

    def get_quote(self, client, message, **kwargs):
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

                users = havocbot.user.find_users_matching_client(word, client.integration_name)
                # logger.debug(users)

                if users is not None and users:
                    for user in users:
                        # is_quote_found_for_user = False

                        if user is not None and user:
                            quote = stasher.get_quote_from_user_id(user.user_id, message.to, self.same_channel_only)
                            if quote is not None:
                                display_quote = self.quote_as_string(quote, user)
                                temp_list.append(display_quote)
                                is_quote_found_for_user = True

                if not is_quote_found_for_user:
                    temp_list.append("No quotes found from user %s" % (word))

            client.send_messages_from_list(temp_list, message.reply(), event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            client.send_message(text, message.reply(), event=message.event)

    def get_quotes(self, client, message, **kwargs):
        stasher = StasherQuote.getInstance()
        stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')
        # logger.debug("stasher_data is '%s'" % (stasher.plugin_data))

        message_list = []
        quotes = stasher.get_quotes()
        if quotes is not None and quotes:
            message_list.append("There are %d known quotes" % (len(quotes)))

            # TEMPORARILY DISABLED
            # for quote in quotes:
            #     display_quote = self.quote_as_string(quote)
            #     if display_quote is not None:
            #         message_list.append(display_quote)
        else:
            message_list.append("There are no known quote")

        client.send_messages_from_list(message_list, message.reply(), event=message.event)

    def search_messages_for_user_match(self, message_list, user_object, client, reverse=None):
        if reverse is True:
            message_list = message_list[::-1]
            # message_list = list(reversed(message_list))  # Another approach

        for message in message_list:
            logger.info("message 0 index is '%s'" % (message[0]))
            logger.info("message 1 index is '%s'" % (message[1]))
            logger.info("message 2 index is '%s'" % (message[2]))
            logger.info("message 3 index is '%s'" % (message[3]))
            logger.info("message 4 index is '%s'" % (message[4]))
            logger.info("message 5 index is '%s'" % (message[5]))
            new_user_object = client.get_user_from_message(message[0], channel=message[2], event=message[3])
            logger.info(new_user_object)

            if new_user_object is not None and new_user_object:
                username = new_user_object.usernames[client.integration_name][0]

                # EDIT101
                # user_temp_list = havocbot.user.get_users_by_username(username, client.integration_name)
                # if user_temp_list is not None and user_temp_list:
                #     for user in user_temp_list:
                #         logger.debug(user)
                #         # Update the user to have the previous username set
                #         user.current_username = username

                user = havocbot.user.get_user_by_username_for_client(username, client.integration_name)
                if user is not None and user:
                    logger.debug(user)
                    # Update the user to have the previous username set
                    user.current_username = username



            if user_object.name is not None and user_object.name and message[0].lower() in user_object.name.lower():
                return message
            elif user_object.current_username is not None and user_object.current_username and message[0].lower() in user_object.current_username.lower():
                return message
            # elif user_object.aliases is not None and user_object.aliases and message[0].lower() in user_object.aliases:
            #     return message
            # XMPP messages include a resource after the JID so need to capture case where the sender includes the resource but the user_id does not
            # elif user_object.user_id.lower() in message[0].lower():
            #     return message

        # for message in message_list:
        #     if message[0].lower() in [user_object.user_id.lower(), user_object.name.lower(), user_object.username.lower()]:
        #         return message
        #     elif user_object.aliases is not None and user_object.aliases and message[0].lower() in user_object.aliases:
        #         return message
        #     # XMPP messages include a resource after the JID so need to capture case where the sender includes the resource but the user_id does not
        #     elif user_object.user_id.lower() in message[0].lower():
        #         return message

        return None

    def add_quote(self, client, message, **kwargs):
        text = "Coming soon"
        client.send_message(text, message.reply(), event=message.event)
        # # Get the results of the capture
        # capture = kwargs.get('capture_groups', None)
        # captured_name = capture[0]
        # users = havocbot.user.find_users_matching_client(captured_name, client.integration_name)
        # logger.info("users are...")
        # logger.info(users)
        # user_that_typed_command = client.get_user_from_message(message.sender, channel=message.to, event=message.event)
        # logger.info("users that typed the command is...")
        # logger.info(user_that_typed_command)

        # if users is not None and users:
        #     for user in users:
        #         if user_that_typed_command is not None and user_that_typed_command:
        #             if user_that_typed_command.user_id == user.user_id:
        #                 text = 'You think you are that noteworthy and can quote yourself? Get outta here'
        #                 client.send_message(text, message.reply(), event=message.event)
        #                 return

        # stasher = StasherQuote.getInstance()
        # stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')

        # is_quote_found_for_user = False

        # if users is not None and users:
        #     for user in users:
        #         if user is not None and user and user.is_valid() is True:
        #             # !addquote bossman
        #             logger.info("about to search messages for user match...")
        #             found_message = self.search_messages_for_user_match(self.recent_messages, user, client, reverse=True)
        #             logger.info("found_message is '%s'" % (str(found_message)))

        #             if found_message is not None and found_message:
        #                 stasher.add_quote(user.user_id, found_message[1], found_message[2], found_message[3], found_message[4])
        #                 text = "%s said something ridiculous. Archived it" % (user.name)
        #                 client.send_message(text, message.reply(), event=message.event)
        #                 is_quote_found_for_user = True
        #             # else:
        #             #     text = "No recent messages found from %s" % (user.name)
        #             #     client.send_message(text, message.reply(), event=message.event)
        #         else:
        #             text = "Unable to find a user matching %s" % (captured_name)
        #             client.send_message(text, message.reply(), event=message.event)

        # if not is_quote_found_for_user:
        #     text = "No recent messages found from %s" % (captured_name)
        #     client.send_message(text, message.reply(), event=message.event)

    # def add_quote(self, client, message, **kwargs):
    #     # Get the results of the capture
    #     capture = kwargs.get('capture_groups', None)
    #     captured_name = capture[0]
    #     user = havocbot.user.find_user_by_id_or_name(captured_name, message.client, client)

    #     user_that_typed_command = client.get_user_from_message(message.sender, channel=message.to, event=message.event)

    #     if user_that_typed_command is not None and user_that_typed_command:
    #         if user_that_typed_command.user_id == user.user_id or user.user_id in user_that_typed_command.user_id:
    #             text = 'You think you are that noteworthy and can quote yourself? Get outta here'
    #             client.send_message(text, message.reply(), event=message.event)
    #             return

    #     stasher = StasherQuote.getInstance()
    #     stasher.plugin_data = stasher.get_plugin_data('havocbot_quoter')

    #     if user is not None and user and user.is_valid() is True:
    #         # !addquote bossman
    #         found_message = self.search_messages_for_user_match(self.recent_messages, user, reverse=True)
    #         logger.info("found_message is '%s'" % (str(found_message)))

    #         if found_message is not None and found_message:
    #             stasher.add_quote(user.user_id, found_message[1], found_message[2], found_message[3], found_message[4])
    #             text = "%s said something ridiculous. Archived it" % (user.name)
    #             client.send_message(text, message.reply(), event=message.event)
    #         else:
    #             text = "No recent messages found from %s" % (user.name)
    #             client.send_message(text, message.reply(), event=message.event)
    #     else:
    #         text = "Unable to find a user matching %s" % (captured_name)
    #         client.send_message(text, message.reply(), event=message.event)

    def debug_quote(self, client, message, **kwargs):
        for message in self.recent_messages:
            logger.info(message)


def format_datetime_for_display(date_object):
    # Convert to local timezone from UTC timezone
    return date_object.astimezone(tz.tzlocal()).strftime("%A %B %d %Y %I:%M%p")


class StasherQuote(Stasher):
    def add_quote(self, user_id, quote, client, channel, timestamp):
        logger.info("Adding new quote - user_id '%s', client '%s', channel '%s', timestamp '%s', quote '%s'" % (user_id, client, channel, timestamp, quote))

        self.plugin_data = self.get_plugin_data('havocbot_quoter')

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

    def get_quote_from_user_id(self, user_id, channel, same_channel_only):
        quote = None

        logger.info("user_id is '%s'" % (user_id))
        logger.info("channel is '%s'" % (channel))
        logger.info("same_channel_only is '%s'" % (same_channel_only))

        if self.plugin_data is not None:
            if 'quotes' in self.plugin_data:
                if same_channel_only:
                    logger.info("we're up here")
                    results = [x for x in self.plugin_data['quotes'] if x['user_id'] == user_id and x['channel'] == channel]
                else:
                    logger.info("we're down here")
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
