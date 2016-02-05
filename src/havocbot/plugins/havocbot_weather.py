#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import weather
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WeatherPlugin(HavocBotPlugin):
    def __init__(self):
        logger.log(0, "__init__ triggered")
        pass

    def init(self, havocbot):
        logger.log(0, "init triggered")
        self.havocbot = havocbot
        self.triggers = {
            ".*\d{5}.*weather|weather.*\d{5}": self.start
        }
        self.help = {
            "description": "fetch weather information for zip codes",
            "usage": (
                ("weather <zip code>", "what is the weather in 94110", "display the current weather for one or more zip codes"),
                ("warmest weather <zip code> <zip code> [<zip code>]", "does 92104 or 10005 have the warmest weather", "find the warmest zip code from a list"),
            )
        }

        # This will register the above triggers with havocbot
        self.havocbot.register_triggers(self.triggers)

    def shutdown(self):
        logger.log(0, "shutdown triggered")
        pass

    def start(self, callback, message, **kwargs):
        words = message.text.split()

        # Capture args that look like zip codes
        zip_codes = []

        for word in words:
            if weather.is_valid_zip_code(word) and word not in zip_codes:
                zip_codes.append(word)

        # Run only if there is at least one zip code
        if len(zip_codes) > 0:
            logger.debug("start - words are %s" % words)
            # Branch if the user wants the warmest weather
            if any(x in ['warmest', 'hottest'] for x in words):
                logger.debug("start - got a match")
                weather_list = weather.return_temperatures_list(zip_codes)
                warmest_weather = weather.return_warmest_weather_object_from_list(weather_list)
                if message.channel:
                    if warmest_weather:
                        callback.send_message(channel=message.channel, message="%s (%s) has the warmest weather of %sF" % (warmest_weather.city, warmest_weather.zip_code, warmest_weather.temperature))
            else:
                weather_list = weather.return_temperatures_list(zip_codes)
                if message.channel:
                    if weather_list:
                        for weather_object in weather_list:
                            callback.send_message(channel=message.channel, message=weather_object.return_weather())
                    else:
                        callback.send_message(channel=message.channel, message="No weather data found")

    # Old style. Ignore
    # def start_strict(self, message):
    #     logger.debug("start - message is '%s'" % (message))

    #     text = message.text.split()
    #     args = text[1:]

    #     if len(args) == 1 and len(args[0]) >= 5:
    #         weather_list = custom.weather.return_temperatures_list(args[0])
    #         if message.channel:
    #             if weather_list:
    #                 for weather_object in weather_list:
    #                     self.havocbot.send_message(message.channel, weather_object.return_weather())
    #             else:
    #                 self.havocbot.send_message(message.channel, "No weather data found")

# Make this plugin available to HavocBot
havocbot_handler = WeatherPlugin()
