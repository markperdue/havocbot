#!/havocbot

from havocbot.plugin import HavocBotPlugin
from plugins import weather
import logging

logger = logging.getLogger(__name__)


class WeatherPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "fetch weather information for zip codes"

    @property
    def plugin_short_name(self):
        return "weather"

    @property
    def plugin_usages(self):
        return [
            ("weather <zip code>", "what is the weather in 94110", "display the current weather for one or more zip codes"),
            ("warmest weather <zip code> <zip code> [<zip code>]", "does 92104 or 10005 have the warmest weather", "find the warmest zip code from a list"),
        ]

    @property
    def plugin_triggers(self):
        return [
            (".*\d{5}.*weather|weather.*\d{5}", self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.api_key_weatherunderground = None
        self.api_key_openweathermap = None
        self.max_zip_codes_per_query = 3  # Default value

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = False

        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'api_key_weatherunderground':
                    self.api_key_weatherunderground = item[1]
                elif item[0] == 'api_key_openweathermap':
                    self.api_key_openweathermap = item[1]

        if (self.api_key_weatherunderground is not None and len(self.api_key_weatherunderground) > 0) or (self.api_key_openweathermap is not None and len(self.api_key_openweathermap) > 0):
            requirements_met = True
        else:
            logger.error('There was an issue with the api key. Verify either an api_key_weatherunderground key is set or an api_key_openweathermap key is set in the settings file')

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

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
                weather_list = weather.return_temperatures_list(zip_codes, self.api_key_weatherunderground, self.api_key_openweathermap, self.max_zip_codes_per_query)
                warmest_weather = weather.return_warmest_weather_object_from_list(weather_list)
                if message.channel:
                    if warmest_weather:
                        callback.send_message(channel=message.channel, message="%s (%s) has the warmest weather of %sF" % (warmest_weather.city, warmest_weather.zip_code, warmest_weather.temperature), event=message.event)
            else:
                weather_list = weather.return_temperatures_list(zip_codes, self.api_key_weatherunderground, self.api_key_openweathermap, self.max_zip_codes_per_query)
                if message.channel:
                    if weather_list:
                        for weather_object in weather_list:
                            callback.send_message(channel=message.channel, message=weather_object.return_weather(), event=message.event)
                    else:
                        callback.send_message(channel=message.channel, message="No weather data found", event=message.event)


# Make this plugin available to HavocBot
havocbot_handler = WeatherPlugin()
