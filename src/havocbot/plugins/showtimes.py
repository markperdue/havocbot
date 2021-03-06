from dateutil import tz, parser
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)


# Python 2.6 does not support total_seconds()
def timedelta_total_seconds(timedelta):
    return (
        timedelta.microseconds +
        (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


class TheatreObject(object):
    def __init__(self, _id=None, name=None, city=None, state=None, movies=None):
        self._id = _id
        self.name = name
        self.city = city
        self.state = state
        self.movies = movies
        self.address = None
        self.postal_code = None
        self.slug = None
        self.website_url = None
        self.attributes = []

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._id == other._id

    def __str__(self):
        return "TheatreObject(ID: %s, Name: %s, City: %s, State: %s)" % (self._id, self.name, self.city, self.state)

    def print_theatre(self):
        print("%s - %s, %s, %s" % (self.name, self.address, self.city, self.state))
        print("    Website: %s" % self.website_url)

    def return_theatre(self):
        return self

    def is_valid(self):
        if not self._id:
            return False
        if not self.city:
            return False
        if not self.state:
            return False

        # All conditions met
        return True


def create_theatre_object_from_json(json):
    theatre = TheatreObject(
        _id=json['id'], name=json['name'], city=json['location']['city'], state=json['location']['state'])

    theatre.website_url = json['websiteUrl'] if 'websiteUrl' in json else None
    if 'location' in json and 'postalCode' in json['location']:
        theatre.postal_code = json['location']['postalCode']
    if 'location' in json and 'addressLine1' in json['location']:
        theatre.address = json['location']['addressLine1']
    theatre.slug = json['slug'] if 'slug' in json else None

    return theatre


class MovieObject(object):
    def __init__(self, _id=None, name=None, synopsis=None, genre=None, has_scheduled_showtimes=None,
                 release_date_utc=None, earliest_showing_utc=None):
        self._id = _id
        self.name = name
        self.synopsis = synopsis
        self.genre = genre
        self.has_scheduled_showtimes = has_scheduled_showtimes
        self.release_date_utc = release_date_utc
        self.earliest_showing_utc = earliest_showing_utc

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._id == other._id

    def __str__(self):
        return "MovieObject(ID: %s, Name: %s, Genre: %s, Has Showtimes: %s, Release Date: %s, Earliest Showing: %s)" % (
            self._id, self.name, self.genre, self.has_scheduled_showtimes,
            self.release_date_utc, self.earliest_showing_utc)

    def print_theatre(self):
        print(self.return_theatre())

    def return_theatre(self):
        return self

    def populate_from_json(self, json):
        if json:
            self._id = json["id"] if "id" in json else None
            self.name = json["name"] if "name" in json else None
            self.synopsis = json["synopsis"] if "synopsis" in json else None
            self.genre = json["genre"] if "genre" in json else None
            self.has_scheduled_showtimes = json["hasScheduledShowtimes"] if "hasScheduledShowtimes" in json else None
            self.release_date_utc = json["releaseDateUtc"] if "releaseDateUtc" in json else None
            self.earliest_showing_utc = json["earliestShowingUtc"] if "earliestShowingUtc" in json else None


class Showtimes(object):
    def __init__(self, showtimes=None, count=None):
        self.showtimes = showtimes
        self.count = count

    def __str__(self):
        return "Showtimes(Count: %d, Showtimes: %s)" % (self.count, self.showtimes)

    def print_showtimes(self):
        print(self.return_showtimes())

    def return_showtimes(self):
        if self.count and self.count > 0 and self.showtimes:
            showtime_string = '(' + '), ('.join(showtime.return_basic() for showtime in self.showtimes) + ')'
            return 'There are %d showtimes - %s' % (self.count, showtime_string)
        else:
            return 'No showtimes found'

    # dt must be timezone aware
    def get_nearest_showtimes_to_datetime(self, dt, max_value):
        nearest_showtimes = []

        if self.count and self.count > 0 and self.showtimes:
            s_list = sorted(self.showtimes, key=lambda x: timedelta_total_seconds(dt - x.get_showtime_as_datetime()))
            # sorted_list = sorted(self.showtimes, key=lambda x: (dt - x.get_showtime_as_datetime()).total_seconds())

            if len(s_list) > max_value:
                for showtime in s_list[:max_value]:
                    nearest_showtimes.append(showtime)
            # else:
            #     nearest_showtimes = nearest_showtimes.append(showtime)

        return nearest_showtimes


class Showtime(object):
    def __init__(self, _id=None, run_time=None, internal_release_number=None, performance_number=None,
                 is_sold_out=None, movie_id=None, movie_name=None,
                 ticket_prices=None, show_date_time_local=None, show_date_time_utc=None):
        self._id = _id
        self.run_time = run_time
        self.internal_release_number = internal_release_number
        self.performance_number = performance_number
        self.is_sold_out = is_sold_out
        self.movie_id = movie_id
        self.movie_name = movie_name
        self.ticket_prices = ticket_prices
        self.show_date_time_local = show_date_time_local
        self.show_date_time_utc = show_date_time_utc
        self.datetime = None
        self.mpaa_rating = None

    def __str__(self):
        return "Showtime(ID: %s, Movie Name: %s, Internal Release Number: %s, Movie ID: %s)" % (
            self._id, self.movie_name, self.internal_release_number, self.movie_id)

    def return_basic(self):
        return "%s - $%s [%s]" % (self.time_as_local(), self.ticket_prices[0].price, self.ticket_prices[0].type_)

    def return_basic_with_name(self):
        return "%s [%s] is showing at %s for $%s" % (
            self.movie_name, self.mpaa_rating, self.time_as_local(), self.ticket_prices[0].price)

    def print_showtime(self):
        print("%s has a UTC showtime of %s and the %s ticket price is %s" % (
            self.movie_name, self.get_showtime_as_datetime(), self.ticket_prices[0].type_, self.ticket_prices[0].price))
        print(self.return_basic())

    def get_showtime_as_datetime(self):
        return parser.parse(self.show_date_time_utc)

    def time_as_local(self):
        date_time = parser.parse(self.show_date_time_utc)

        # Assert the current time is in UTC
        date_time = date_time.replace(tzinfo=tz.tzutc())

        # Convert to local time
        return date_time.astimezone(tz.tzlocal()).strftime('%I:%M:%S%p')


class ShowtimeTicket(object):
    def __init__(self, price=None, type_=None, sku=None, age_policy=None):
        self.price = price
        self.type_ = type_
        self.sku = sku
        self.age_policy = age_policy

    def __str__(self):
        return "Ticket(Price: %s, Type: %s, SKU: %s)" % (self.price, self.type_, self.sku)


def get_json_showtimes_at_theatre_on_date(theatre_object, date, api_key_amc):
    headers = {'X-AMC-Vendor-Key': api_key_amc}
    url = "https://api.amctheatres.com/v2/theatres/%s/showtimes/%s/?pageSize=25" % (theatre_object._id, date)

    logger.debug("Fetching showtimes at %s on %s..." % (theatre_object._id, date))

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()
    else:
        return None


def get_json_showtimes_at_theatre_on_date_for_movie(theatre_object, date, movie_name, api_key_amc):
    headers = {'X-AMC-Vendor-Key': api_key_amc}
    url = "https://api.amctheatres.com/v2/theatres/%s/showtimes/%s/?movieName=%s&pageSize=25" % (
        theatre_object._id, date, movie_name)

    logger.debug("Fetching showtimes at %s on %s for %s..." % (theatre_object._id, date, movie_name))

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()
    else:
        return None


def ticket_as_payload(json):
    return ShowtimeTicket(price=json['price'], type_=json['type'], sku=json['sku'])


def create_showtime_from_json(data):
    if data is not None:
        showtime = Showtime()

        showtime._id = data['id'] if 'id' in data else None
        showtime.run_time = data['runTime'] if 'runTime' in data else None
        showtime.internal_release_number = data['internalReleaseNumber'] if 'internalReleaseNumber' in data else None
        showtime.performance_number = data['performanceNumber'] if 'performanceNumber' in data else None
        showtime.is_sold_out = data['isSoldOut'] if 'isSoldOut' in data else None
        showtime.mpaa_rating = data['mpaaRating'] if 'mpaaRating' in data else None
        showtime.movie_id = data['movieId'] if 'movieId' in data else None
        showtime.movie_name = data['movieName'] if 'movieName' in data else None
        showtime.show_date_time_local = data['showDateTimeLocal'] if 'showDateTimeLocal' in data else None
        showtime.show_date_time_utc = data['showDateTimeUtc'] if 'showDateTimeUtc' in data else None

        ticket_prices_list = []
        for ticket_data in data['ticketPrices']:
            ticket = ticket_as_payload(ticket_data)
            ticket_prices_list.append(ticket)
        showtime.ticket_prices = ticket_prices_list

        return showtime
    else:
        return None


def get_location_suggestions(zip_code, api_key_amc):
    logger.info("Fetching location suggestions for %s..." % zip_code)

    headers = {'X-AMC-Vendor-Key': api_key_amc}
    url = "https://api.amctheatres.com/v2/location-suggestions/?query=%s" % zip_code

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()
    else:
        return None


def parse_location_suggestions_for_locations_url(json):
    url = None

    if json is not None:
        if '_embedded' in json:
            if 'suggestions' in json['_embedded']:
                for item in json['_embedded']['suggestions']:
                    if '_links' in item:
                        if 'https://api.amctheatres.com/rels/v2/locations' in item['_links']:
                            if 'href' in item['_links']['https://api.amctheatres.com/rels/v2/locations']:
                                url = item['_links']['https://api.amctheatres.com/rels/v2/locations']['href']

    if url is not None and 'https://api.amctheatres.com' in url and len(url) > 30:
        return url
    else:
        return None


def parse_locations_for_theatre_objects_within_distance(json, distance):
    theatre_objects_list = []

    if json is not None:
        if '_embedded' in json:
            if 'locations' in json['_embedded']:
                for location in json['_embedded']['locations']:
                    if 'distance' in location:
                        if float(location['distance']) < distance:
                            raw_theatre = location['_embedded']['theatre']
                            theatre = create_theatre_object_from_json(raw_theatre)
                            theatre_objects_list.append(theatre)

    return theatre_objects_list


def get_theater_id_list_from_locations_url(url, api_key_amc):
    if url is not None and 'https://api.amctheatres.com' in url and len(url) > 30:
        logger.info("Fetching locations at %s..." % url)

        headers = {'X-AMC-Vendor-Key': api_key_amc}

        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            return r.json()
        else:
            return None


def get_showtimes_for_zip_on_date(zip_code, date, api_key_amc, max_distance, max_upcoming_st):
    results = []
    if zip_code is not None and date is not None and api_key_amc is not None \
            and max_distance is not None and max_upcoming_st is not None:
        location_suggestions = get_location_suggestions(zip_code, api_key_amc)
        locations_url = parse_location_suggestions_for_locations_url(location_suggestions)

        if locations_url is not None:
            locations_json = get_theater_id_list_from_locations_url(locations_url, api_key_amc)
            theatre_list = parse_locations_for_theatre_objects_within_distance(locations_json, max_distance)

            # We now have some theaters within the max distance of the zip code
            for theatre in theatre_list:
                results.append("Upcoming showtimes at %s" % theatre.name)
                showtimes_list = get_showtimes_list_for_theatre_object_and_date(theatre, date, api_key_amc)

                if showtimes_list is not None:
                    now = datetime.utcnow().replace(tzinfo=tz.tzutc())
                    nearest_showtimes_list = showtimes_list.get_nearest_showtimes_to_datetime(now, max_upcoming_st)
                    if nearest_showtimes_list is not None:
                        for showtime in nearest_showtimes_list:
                            # print(showtime.return_basic_with_name())
                            results.append("    %s" % (showtime.return_basic_with_name()))

    if len(results) == 0:
        results.append('No showtimes found')

    return results


def get_showtimes_list_for_theatre_object_and_date(theatre_object, date, api_key_amc):
    data = get_json_showtimes_at_theatre_on_date(theatre_object, date, api_key_amc)

    if data is not None:
        showtimes = Showtimes()
        if 'count' in data:
            showtimes.count = data['count']

        # Create a list of showtimes
        showtimes_list = []
        if '_embedded' in data and 'showtimes' in data['_embedded']:
            for item in data['_embedded']['showtimes']:
                showtime = create_showtime_from_json(item)
                showtimes_list.append(showtime)
            showtimes.showtimes = showtimes_list

        return showtimes
    else:
        logger.error("Data not valid")
        # print("Data not valid")

        return None


def main():
    zip_code = "94110"
    showtimes = get_showtimes_for_zip_on_date(zip_code, datetime.now().strftime("%m-%d-%Y"), None, None, None)
    if showtimes is not None:
        for listing in showtimes:
            print(listing)
    else:
        print("No showtimes found")


if __name__ == "__main__":
    main()
