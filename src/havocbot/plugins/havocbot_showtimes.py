#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import showtimes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShowtimesPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "display showtimes for a search query at the SF Metreon"

    @property
    def plugin_short_name(self):
        return "showtimes"

    @property
    def plugin_usages(self):
        return [
            ("movies in <zip code>", "movies in 94110", "displays the earliest upcoming movie showtimes in a zip code"),
        ]

    @property
    def plugin_triggers(self):
        return [
            (".*movies in\s*(\d{5})", self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        # Capture the zip code
        capture = kwargs.get('capture_groups', None)
        zip_code = capture[0]
        logger.debug("start - searching for movies for '%s'" % (zip_code))
        showtimes_object = showtimes.get_showtimes_for_zip_on_date(zip_code, datetime.now().strftime("%m-%d-%Y"))
        if message.channel:
            if showtimes_object:
                callback.send_messages_from_list(channel=message.channel, message=showtimes_object)
            else:
                callback.send_message(channel=message.channel, message="No showtime data found")


# Make this plugin available to HavocBot
havocbot_handler = ShowtimesPlugin()
