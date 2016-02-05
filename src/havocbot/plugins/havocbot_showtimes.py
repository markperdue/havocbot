#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import showtimes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ShowtimesPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            ".*showtimes for\s*(.*)": self.start
        }
        self.help = {
            "description": "display showtimes for a search query at the SF Metreon",
            "usage": (
                ("showtimes for <movie name>", "get me showtimes for star wars", "look up showtimes for a movie"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        # "get me weather in 94010 and 94110"
        # "find me the warmest weather between 94010 and 94110"

        logger.debug("start - message is '%s'" % (message))

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
