#!/havocbot

from dateutil import tz, parser
import logging
import random
from tinydb import TinyDB, Query
from havocbot.exceptions import FormattedMessageNotSentError
from havocbot.message import FormattedMessage
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.user import UserDataAlreadyExistsException, UserDataNotFoundException, UserDoesNotExist

logger = logging.getLogger(__name__)


class QuoterPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'quote management'

    @property
    def plugin_short_name(self):
        return 'quoter'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!quote get <name>', example='!quote get mark', description='get a quote said by a user'),
            Usage(command='!addquote <name>', example='!addquote markaperdue',
                  description='add the last message said by the user to storage'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!quote\sget-id\s([0-9]+)', function=self.trigger_get_quote_by_id, requires=None),
            Trigger(match='!quote\sget\s(.*)', function=self.trigger_get_quotes_by_user_search, requires=None),
            Trigger(match='!addquote\s(.*)', function=self.trigger_add_quote, requires=None),
            Trigger(match='!debugquote', function=self.trigger_debug_quote, requires=None),
            Trigger(match='(.*)', function=self.trigger_default, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.recent_messages = []
        self.max_messages_per_user_per_channel = 5
        self.same_channel_only = False
        self.stasher = StasherTinyDBQuoter()

    def configure(self, settings):
        requirements_met = True

        if settings is not None and settings:
            for item in settings:
                if item[0] == 'same_channel_only':
                    self.same_channel_only = item[1]

        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def trigger_default(self, client, message, **kwargs):
        if message.text.startswith(('!addquote', '!debugquote')):
            return

        # Count occurrences of messages by a user in a client integration
        previous_messages = [x for x in self.recent_messages
                             if x.sender == message.sender and x.client == message.client and x.to == message.to]

        logger.debug('%d tracked messages for %s in channel %s' % (len(previous_messages), message.sender, message.to))

        if len(previous_messages) >= self.max_messages_per_user_per_channel:
            try:
                self.recent_messages.remove(previous_messages[0])
            except ValueError:
                pass

        logger.debug('Adding message by user %s to recent messages' % message.sender)
        self.recent_messages.append(message)

    def _get_quote_formatted_message(self, user, quote):
        time = format_datetime_for_display(parser.parse(quote['timestamp'])) if 'timestamp' in quote else 'Unknown'

        return FormattedMessage(
            text='"%s"' % (quote['quote']),
            fallback_text=self._quote_as_string(quote),
            title='%s - %s' % (user.name, time),
            thumbnail_url=user.image
        )

    def trigger_get_quote_by_id(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_json_id = int(capture[0])

        try:
            a_tuple = self._get_quote_by_id_with_user_resolved(captured_json_id)
        except UserDoesNotExist:
            text = 'That user does not exist'
            client.send_message(text, message.reply(), event=message.event)
        except UserDataNotFoundException:
            text = 'No quote found with ID %d' % (int(captured_json_id))
            client.send_message(text, message.reply(), event=message.event)
        else:
            user = a_tuple[0]
            quote = a_tuple[1]

            if user is not None and quote is not None:
                f_message = self._get_quote_formatted_message(user, quote)

                try:
                    client.send_formatted_message(f_message, message.reply(), event=message.event, style='thumbnail')
                except FormattedMessageNotSentError as e:
                    logger.error("Unable to send formatted message with payload '%s'" % e)

                    text = self._quote_as_string(quote, user)
                    client.send_message(text, message.reply(), event=message.event)

    def trigger_add_quote(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_username = capture[0]

        users = self.havocbot.db.find_users_by_matching_string_for_client(captured_username, client.integration_name)
        if users is not None and users:
            for user in users:
                try:
                    self._add_most_recent_quote_from_user(user, client, self.recent_messages)
                except UserDataNotFoundException:
                    text = 'No previously tracked messages found from that user'
                    client.send_message(text, message.reply(), event=message.event)
                except UserDataAlreadyExistsException:
                    text = 'That message has already been added'
                    client.send_message(text, message.reply(), event=message.event)

    def trigger_get_quotes_by_user_search(self, client, message, **kwargs):
        capture = kwargs.get('capture_groups', None)
        captured_names = capture[0]
        words = captured_names.split()

        if len(words) <= 5:

            for word in words:
                is_user_found = False
                matched_users = []

                users = self.havocbot.db.find_users_by_matching_string_for_client(word, client.integration_name)
                if users is not None and users:
                    matched_users.extend(users)
                    is_user_found = True

                if not is_user_found:
                    text = 'User %s was not found' % word
                    client.send_message(text, message.reply(), event=message.event)

                if matched_users:
                    set_users = set(matched_users)
                    for user in set_users:
                        if self.same_channel_only == 'True':
                            quote = self.stasher.find_quote_by_user_id_in_channel(user.user_id, message.to)
                        else:
                            quote = self.stasher.find_quote_by_user_id(user.user_id)

                        if quote is not None and quote:
                            formatted_message = self._get_quote_formatted_message(user, quote)

                            try:
                                client.send_formatted_message(formatted_message, message.reply(), event=message.event,
                                                              style='thumbnail')
                            except FormattedMessageNotSentError as e:
                                logger.error("Unable to send formatted message with payload '%s'" % e)

                                text = self._quote_as_string(quote, user)
                                client.send_message(text, message.reply(), event=message.event)

                        else:
                            text = 'No quotes found from user %s' % word
                            client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Too many parameters. What are you trying to do?'
            client.send_message(text, message.reply(), event=message.event)

    def trigger_debug_quote(self, client, message, **kwargs):
        for message in self.recent_messages:
            logger.info(message)

    def _add_most_recent_quote_from_user(self, user, client, message_list):
        try:
            self._search_user_and_client_in_message(user, client, message_list, reverse=True)
        except:
            raise

    def _search_user_and_client_in_message(self, user, client, message_list, reverse=None):
        if reverse is True:
            message_list.reverse()

        for message in message_list:
            if client.integration_name in user.usernames and user.usernames[client.integration_name] is not None:
                if message.sender in user.usernames[client.integration_name]:
                    self._add_quote(message)
                    return

        raise UserDataNotFoundException

    def _add_quote(self, message):
        logger.info('Adding %s to quote db' % message)

    def _quote_as_string(self, quote_dict, user_object=None):
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

    # def _get_quote_by_id_with_user_resolved(self, json_id):
    #     display_quote = None
    #
    #     result = self._get_quote_by_id(int(json_id))
    #     if result is not None and result:
    #         user = None
    #         if 'user_id' in result and result['user_id'] is not None and result['user_id'] > 0:
    #             user = self.havocbot.db.find_user_by_id(result['user_id'])
    #
    #         display_quote = self._quote_as_string(result, user)
    #     else:
    #         display_quote = 'No quote found with ID %d' % (int(json_id))
    #
    #     return display_quote

    def _get_quote_by_id_with_user_resolved(self, json_id):
        try:
            result = self._get_quote_by_id(int(json_id))
        except Exception:
            raise
        else:
            if result is not None and result:
                if 'user_id' in result and result['user_id'] is not None and result['user_id'] > 0:

                    try:
                        user = self.havocbot.db.find_user_by_id(result['user_id'])
                    except UserDoesNotExist:
                        raise
                    else:
                        return user, result

    def _get_quote_by_id(self, json_id):
        return self.stasher.find_quote_by_id(int(json_id))

    # def _get_quotes_by_ids(self, client, message, **kwargs):
    #     # Get the results of the capture
    #     capture = kwargs.get('capture_groups', None)
    #     captured_json_ids = capture[0]
    #     json_ids = captured_json_ids.split()
    #
    #     if len(json_ids) <= 5:
    #         temp_list = []
    #
    #         for json_id in json_ids:
    #             temp_list.append(self._get_quote_by_id_with_user_resolved(int(json_id)))
    #
    #         client.send_messages_from_list(temp_list, message.reply(), event=message.event)
    #     else:
    #         text = 'Too many parameters. What are you trying to do?'
    #         client.send_message(text, message.reply(), event=message.event)


def format_datetime_for_display(date_object):
    # Convert to local timezone from UTC timezone
    return date_object.astimezone(tz.tzlocal()).strftime('%A %B %d %Y %I:%M%p')


class StasherTinyDBQuoter(object):
    def __init__(self):
        self.db = TinyDB('stasher/havocbot_quoter.json', default_table='quotes', sort_keys=True, indent=2)

    def find_quote_by_id(self, json_id):
        logger.info("Searching for json object with id '%d'" % json_id)

        result = self.db.get(eid=json_id)

        logger.debug("Returning with '%s'" % result)
        return result

    def find_quote_by_user_id(self, user_id):
        logger.info("Searching for quote from user id '%d'" % user_id)
        result = None

        quotes_query = Query()
        matched_quotes = self.db.search(quotes_query['user_id'] == user_id)
        if matched_quotes is not None and matched_quotes:
            result = random.choice(matched_quotes)

        logger.debug("Returning with '%s'" % result)
        return result

    def find_quote_by_user_id_in_channel(self, user_id, channel):
        logger.info("Searching for quote from user id '%d' in channel '%s'" % (user_id, channel))
        result = None

        quotes_query = Query()
        matched_quotes = self.db.search((quotes_query['user_id'] == user_id) & (quotes_query['channel'] == channel))
        if matched_quotes is not None and matched_quotes:
            result = random.choice(matched_quotes)

        logger.debug("Returning with '%s'" % result)
        return result


# Make this plugin available to HavocBot
havocbot_handler = QuoterPlugin()
