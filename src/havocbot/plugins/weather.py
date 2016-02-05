import argparse
from datetime import datetime
from dateutil import tz
import logging
import logging.handlers
import requests
import sys
from xml.etree import ElementTree


API_KEY_WU = ""  # Enter WeatherUnderground API key here
API_KEY_OW = ""  # Enter OpenWeathermap API key here
MAX_ZIP_CODES_PER_QUERY = 3

logger = logging.getLogger(__name__)


class WeatherObject():
    def __init__(self, zip_code, temperature, city=None, state=None, source="MockData", last_updated=(datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()):
        self.zip_code = zip_code
        self.temperature = temperature
        self.city = city
        self.state = state
        self.source = source
        self.last_updated = last_updated  # UTC epoch seconds

    # Two temperatures are considered equal if they have the same zip code. Bad
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.zip_code == other.zip_code)

    def __str__(self):
        return "WeatherObject(Zip Code: %s, City: %s, State: %s, Temperature: %s, Last Updated: %s])" % (self.zip_code, self.city, self.state, self.temperature, self.last_updated)

    def print_weather(self):
        print(self.return_weather())

    def return_weather(self):
        if self.last_updated:
            return "The temperature is %sF (%sC) in %s [last updated: %s by %s)" % (self.temperature, self.temperature_in_celsius(), self.city, self.time_as_local(), self.source)
        else:
            return "The temperature is %sF (%sC) in %s [%s]" % (self.temperature, self.temperature_in_celsius(), self.city, self.source)

    def temperature_in_celsius(self):
        return round((float(self.temperature) - 32) * 5/9, 2)

    def is_valid(self):
        if not self.temperature:
            return False
        if not self.zip_code:
            return False
        if not self.city:
            return False
        if not self.last_updated:
            return False

        # All conditions met
        return True

    def time_as_local(self):
        utc = datetime.utcfromtimestamp(self.last_updated)

        # Assert the current time is in UTC
        utc = utc.replace(tzinfo=tz.tzutc())

        # Convert to local time
        return utc.astimezone(tz.tzlocal()).strftime('%b %d %Y %I:%M:%S%p')


def create_weather_from_openweathermap_for_zip_code(zip_code):
    source = "OpenWeatherMap"
    data = get_openweathermap_xml_for_zip_code(zip_code)

    if data is not None and is_valid_openweathermap_data(data):
        temperature = data.find('temperature').get('value')
        city = data.find('city').get('name')
        date_raw = data.find('lastupdate').get('value')

        # Convert from 2015-08-27T05:21:06 to seconds since epoch
        date_time = datetime.strptime(date_raw, '%Y-%m-%dT%H:%M:%S')
        epoch_seconds = (date_time - datetime.utcfromtimestamp(0)).total_seconds()

        return WeatherObject(zip_code=zip_code, temperature=temperature, city=city, source=source, last_updated=float(epoch_seconds))
    else:
        logger.error("Invalid weather data for zip code %s" % (zip_code))
        print("Invalid weather data for zip code %s" % (zip_code))

        return None


def create_weather_from_weatherunderground_for_zip_code(zip_code):
    source = "WeatherUnderground"
    data = get_weather_underground_data_for_zip_code(zip_code)

    if data is not None and is_valid_wu_weather(data):
        return WeatherObject(zip_code=zip_code, temperature=data['current_observation']['temp_f'], city=data['current_observation']['display_location']['city'], state=data['current_observation']['display_location']['state'], source=source, last_updated=float(data['current_observation']['observation_epoch']))
    else:
        logger.error("Invalid weather data for zip code %s" % (zip_code))
        print("Invalid weather data for zip code %s" % (zip_code))

        return None


def get_openweathermap_xml_for_zip_code(zip_code):
    logger.info("Fetching OpenWeatherMap data for zip code %s..." % (zip_code))

    r = requests.get('http://api.openweathermap.org/data/2.5/weather?zip=%s,us&mode=xml&units=imperial' % (zip_code))

    if r.status_code == 200:
        try:
            response = ElementTree.fromstring(r.content)
        except ElementTree.ParseError:
            response = None

        return response
    else:
        return None


def get_weather_underground_data_for_zip_code(zip_code):
    logger.info("Fetching WeatherUnderground data for zip code %s..." % (zip_code))

    r = requests.get('http://api.wunderground.com/api/%s/conditions/q/%s.json' % (API_KEY_WU, zip_code))

    if r.status_code == 200:
        return r.json()
    else:
        return None


# Checks to see if the json response contains certain required elements to print
def is_valid_wu_weather(json):
    if json is None:
        return False
    if 'current_observation' not in json:
        return False
    if 'temp_f' not in json['current_observation']:
        return False
    if 'full' not in json['current_observation']['display_location']:
        return False
    if 'city' not in json['current_observation']['display_location']:
        return False
    if 'state' not in json['current_observation']['display_location']:
        return False
    if 'observation_epoch' not in json['current_observation']:
        return False
    if 'zip' not in json['current_observation']['display_location']:
        return False

    # All conditions met
    return True


def is_valid_openweathermap_data(xml):
    temperature = xml.find('temperature').get('value')
    city = xml.find('city').get('name')
    date_raw = xml.find('lastupdate').get('value')

    if not temperature:
        return False
    if not city:
        return False
    if not date_raw:
        return False

    # All conditions met
    return True


def is_valid_zip_code(zip_code):
    if len(str(zip_code)) == 5 and zip_code.isdigit():
        return True
    else:
        return False


def print_warmest_weather_from_list(weather_objects):
    warmest_weather = return_warmest_weather_object_from_list(weather_objects)
    if warmest_weather:
        print("\n%s, %s (%s) has the warmest weather of %sF" % (warmest_weather.city, warmest_weather.state, warmest_weather.zip_code, warmest_weather.temperature))
    else:
        print("No locations found")


def print_weather_list(weather_objects):
    for item in weather_objects:
        item.print_weather()


def return_warmest_weather_object_from_list(weather_objects):
    # Default value
    warmest_weather_object = None

    for item in weather_objects:
        if warmest_weather_object is None or item.temperature > warmest_weather_object.temperature:
            warmest_weather_object = item

    return warmest_weather_object


def return_most_recent_weather_object_from_list(weather_objects):
    # Default value
    most_recent_weather_object = None

    for item in weather_objects:
        if most_recent_weather_object:
            logger.debug("Comparing timestamp %s (%s) against %s (%s)" % (item.last_updated, item.source, most_recent_weather_object.last_updated, most_recent_weather_object.source))

        if most_recent_weather_object is None or item.last_updated > most_recent_weather_object.last_updated:
            most_recent_weather_object = item

    # Mostly just informational
    if most_recent_weather_object:
        logger.info("%s has the most recent updated temperature for %s" % (most_recent_weather_object.source, most_recent_weather_object.zip_code))

        return most_recent_weather_object
    else:
        return None


def return_zip_code_string_from_file(filepath):
    data = None

    try:
        with open(filepath, "r") as myfile:
            data = myfile.read().replace('\n', '')
    except IOError:
        logger.error("Unable to find file")
        print("Unable to find file")

    if data:
        return data
    else:
        return None


def parse_args_and_return():
    parser = argparse.ArgumentParser(description='Fetch weather for one or many zip codes')
    parser.add_argument('-z', '--zip-code', help='comma seperated list of zip codes', required=False)
    parser.add_argument('-f', '--file', help='file containing comma seperated list of zip codes', required=False)
    parser.add_argument('-v', '--verbose', help='enable verboes logging', required=False, action='store_true')
    args = vars(parser.parse_args())

    if args['verbose']:
        logging.basicConfig(level="DEBUG", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        # logging.basicConfig(level="INFO", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        pass

    # Deal with both zip_code and file args being provided. Exit
    if args['zip_code'] and args['file']:
        print("Ambiguous input. Cannot use both --zip-code and --file options")
        sys.exit(1)

    return args


def return_zip_code_list_from_input(args):
    if args['zip_code'] and len(args['zip_code']) >= 5:
        zip_code_string = args['zip_code']
    elif args['file']:
        zip_code_string = return_zip_code_string_from_file(args['file'])
    else:
        zip_code_string = raw_input('Enter a comma separated list of zip codes (ex. 94110, 80123): ')

    # Exit if no values provided by user
    if not zip_code_string:
        print("No values provided. Exiting")
        sys.exit(1)

    # Create a list from the string
    zip_code_list = zip_code_string.split(',')

    return zip_code_list


def add_most_recent_weather_in_list_to_master_list(new_list, master_list):
    most_recent_weather_object = return_most_recent_weather_object_from_list(new_list)

    if most_recent_weather_object and most_recent_weather_object.is_valid():
        # Add the result
        master_list.append(most_recent_weather_object)
    else:
        logger.debug("No recent weather objects found")


def return_temperatures_list(zip_code_list):
    temperatures = []

    # Fetch weather data for the zip codes in the global list
    if len(zip_code_list) > MAX_ZIP_CODES_PER_QUERY:
        logger.debug("Too many zip codes requested. Fetching only the first %d elements" % (MAX_ZIP_CODES_PER_QUERY))

    for item in zip_code_list[:MAX_ZIP_CODES_PER_QUERY]:
        # Strip off spaces if the user provided them during input
        zip_code_temp = item.strip()

        if is_valid_zip_code(zip_code_temp):
            # Create an empty list
            sources = []

            # Get data from WeatherUnderground
            weather = create_weather_from_weatherunderground_for_zip_code(zip_code_temp)
            if weather:
                sources.append(weather)

            # Get data from OpenWeatherMap
            weather_alt = create_weather_from_openweathermap_for_zip_code(zip_code_temp)
            if weather_alt:
                sources.append(weather_alt)

            add_most_recent_weather_in_list_to_master_list(sources, temperatures)
        else:
            logger.debug("'%s' is not a valid zip code" % (zip_code_temp))

    return temperatures


def main():
    # Deal with command line arguments
    args = parse_args_and_return()

    # Create a list of zip codes from input
    zip_code_list = return_zip_code_list_from_input(args)

    # Create a list of temperature objects from a zip code list
    temperatures = return_temperatures_list(zip_code_list)

    # Print the weather list
    print_weather_list(temperatures)

    # Print the warmest place I should go to
    print_warmest_weather_from_list(temperatures)


if __name__ == "__main__":
    main()
