#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import showtimes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShowtimesPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "display upcoming showtimes for theaters (AMC only)"

    @property
    def plugin_short_name(self):
        return "showtimes"

    @property
    def plugin_usages(self):
        return [
            ("movies in <zip code>", "movies in 94110", "displays the earliest upcoming movie showtimes in a zip code (AMC only)"),
        ]

    @property
    def plugin_triggers(self):
        return [
            (".*movies in\s*(\d{5})", self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.api_key_amc = None
        self.max_distance_in_miles = 5  # Default option
        self.max_upcoming_showtimes_to_display = 5  # Default option

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'api_key_amc':
                    self.api_key_amc = item[1]
                elif item[0] == 'max_distance_in_miles':
                    self.max_distance_in_miles = item[1]
                elif item[0] == 'max_upcoming_showtimes_to_display':
                    self.max_upcoming_showtimes_to_display = item[1]

        if self.api_key_amc is not None and len(self.api_key_amc) > 0:
            if self.max_distance_in_miles is not None and isinstance(self.max_distance_in_miles, int):
                if self.max_upcoming_showtimes_to_display is not None and isinstance(self.max_upcoming_showtimes_to_display, int):
                    requirements_met = True
                else:
                    logger.error('There was an issue with the max_upcoming_showtimes_to_display setting. Verify that the max_upcoming_showtimes_to_display key is set in the settings file')
            else:
                logger.error('There was an issue with the max_distance_in_miles setting. Verify that the max_distance_in_miles key is set in the settings file')
        else:
            logger.error('There was an issue with the api key. Verify that the api_key_amc key is set in the settings file')

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        # Capture the zip code
        capture = kwargs.get('capture_groups', None)
        zip_code = capture[0]
        logger.debug("start - searching for movies for '%s'" % (zip_code))
        showtimes_object = showtimes.get_showtimes_for_zip_on_date(zip_code, datetime.now().strftime("%m-%d-%Y"), self.api_key_amc, self.max_distance_in_miles, self.max_upcoming_showtimes_to_display)
        if message.channel:
            if showtimes_object:
                callback.send_messages_from_list(channel=message.channel, message=showtimes_object, event=message.event)
            else:
                callback.send_message(channel=message.channel, message="No showtime data found", event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = ShowtimesPlugin()
