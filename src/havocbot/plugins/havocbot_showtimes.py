#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import showtimes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ShowtimesPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "display showtimes for a search query at the SF Metreon"

    @property
    def plugin_short_name(self):
        return "showtimes"

    @property
    def plugin_usages(self):
        return (
            ("showtimes for <movie name>", "get me showtimes for star wars", "look up showtimes for a movie"),
        )

    @property
    def plugin_triggers(self):
        return (
            (".*showtimes for\s*(.*)", self.start),
        )

    def init(self, havocbot):
        self.havocbot = havocbot

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.plugin_triggers)

    def shutdown(self):
        self.havocbot.unregister_triggers(self.plugin_triggers)
        self.havocbot = None

    def start(self, callback, message, **kwargs):
        # "get me weather in 94010 and 94110"
        # "find me the warmest weather between 94010 and 94110"

        # Capture the movie name
        capture = kwargs.get('capture_groups', None)
        movie_name = '+'.join(capture[0].split())
        logger.debug("start - searching for '%s'" % (movie_name))
        showtimes_object = showtimes.create_showtimes("2325", datetime.now().strftime("%m-%d-%Y"), movie_name)
        if message.channel:
            if showtimes_object:
                callback.send_message(channel=message.channel, message=showtimes_object.return_showtimes())
            else:
                callback.send_message(channel=message.channel, message="No showtime data found")


# Make this plugin available to HavocBot
havocbot_handler = ShowtimesPlugin()
