from dateutil import tz, parser
import json
import logging
import requests
import time

API_KEY_AMC = ""  # Enter WeatherUnderground API key here
API_KEY_HEADER = "X-AMC-Vendor-Key"
AMC_METREON_16 = "2325"

logger = logging.getLogger(__name__)


class TheatreObject(object):
    def __init__(self, id=None, city=None, state=None, movies=None):
        self.id = id
        self.city = city
        self.state = state
        self.movies = movies

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.id == other.id)

    def __str__(self):
        return "TheatreObject(ID: %s, City: %s, State: %s, Movies Available: %d)" % (self.id, self.city, self.state, len(self.movies))

    def print_theatre(self):
        print(self.return_theatre())

    def return_theatre(self):
        return self

    def is_valid(self):
        if not self.id:
            return False
        if not self.city:
            return False
        if not self.state:
            return False
        if not self.last_updated:
            return False

        # All conditions met
        return True


class MovieObject(object):
    def __init__(self, id_=None, name=None, synopsis=None, genre=None, has_scheduled_showtimes=None, release_date_utc=None, earliest_showing_utc=None):
        self.id_ = id_
        self.name = name
        self.synopsis = synopsis
        self.genre = genre
        self.has_scheduled_showtimes = has_scheduled_showtimes
        self.release_date_utc = release_date_utc
        self.earliest_showing_utc = earliest_showing_utc

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.id == other.id)

    def __str__(self):
        return "MovieObject(ID: %s, Name: %s, Genre: %s, Has Showtimes: %s, Release Date: %s, Earliest Showing: %s)" % (self.id_, self.name, self.genre, self.has_scheduled_showtimes, self.release_date_utc, self.earliest_showing_utc)

    def print_theatre(self):
        print(self.return_theatre())

    def return_theatre(self):
        return self

    def populate_from_json(self, json):
        if json:
            self.id_ = json["id"] if "id" in json else None
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
        if self.count and self.count > 0 and self.showtimes and len(self.showtimes) > 0:
            showtime_string = '(' + '), ('.join(showtime.return_basic() for showtime in self.showtimes) + ')'
            return 'There are %d showtimes - %s' % (self.count, showtime_string)
        else:
            return 'No showtimes found'


class Showtime(object):
    def __init__(self, id_=None, run_time=None, internal_release_number=None, performance_number=None, is_sold_out=None, movie_id=None, movie_name=None, ticket_prices=None, show_date_time_local=None, show_date_time_utc=None):
        self.id_ = id_
        self.run_time = run_time
        self.internal_release_number = internal_release_number
        self.performance_number = performance_number
        self.is_sold_out = is_sold_out
        self.movie_id = movie_id
        self.movie_name = movie_name
        self.ticket_prices = ticket_prices
        self.show_date_time_local = show_date_time_local
        self.show_date_time_utc = show_date_time_utc

    def __str__(self):
        return "Showtime(ID: %s, Movie Name: %s, Internal Release Number: %s, Movie ID: %s)" % (self.id_, self.movie_name, self.internal_release_number, self.movie_id)

    def return_basic(self):
        return "%s - $%s [%s]" % (self.time_as_local(), self.ticket_prices[0].price, self.ticket_prices[0].type_)

    def print_showtime(self):
        print("%s has a local showtime of %s and the %s ticket price is %s" % (self.movie_name, self.show_date_time_utc, self.ticket_prices[0].type_, self.ticket_prices[0].price))

    def time_as_local(self):
        date_time = parser.parse(self.show_date_time_utc)

        # Assert the current time is in UTC
        date_time = date_time.replace(tzinfo=tz.tzutc())

        # Convert to local time
        return date_time.astimezone(tz.tzlocal()).strftime('%b %d %Y %I:%M:%S%p')


class ShowtimeTicket(object):
    def __init__(self, price=None, type_=None, sku=None, age_policy=None):
        self.price = price
        self.type_ = type_
        self.sku = sku
        self.age_policy = age_policy

    def __str__(self):
        return "Ticket(Price: %s, Type: %s, SKU: %s)" % (self.price, self.type_, self.sku)


class ShowtimeTask(object):
    def __init__(self, created_by, city=None, state=None, title=None):
        self.created_by = created_by
        self.created_on = time.time()
        self.city = city
        self.state = state
        self.title = title

    def __str__(self):
        return "ShowtimeTask(Created By: '%s', City: '%s', Title: '%s')" % (self.created_by, self.city, self.title)

    def get_city(self):
        city_string = raw_input('What city should we look for?: ')
        self.city = city_string

    def get_state(self):
        state_string = raw_input('What state should we look for?: ')
        self.state = state_string

    def get_title(self):
        title_string = raw_input('What movie title should we look for?: ')
        self.title = title_string

    def is_valid(self):
        # if not self.city:
        #     return False
        if not self.title:
            return False

        return True


def get_json_showtimes_at_theatre_on_date_for_movie(theatre_id, date, movie_name):
    logger.info("Fetching showtimes at %s on %s for %s..." % (theatre_id, date, movie_name))

    headers = {'X-AMC-Vendor-Key': API_KEY_AMC}
    r = requests.get('https://api.amctheatres.com/v2/theatres/%s/showtimes/%s/?movie=%s&pageSize=25' % (theatre_id, date, movie_name), headers=headers)

    if r.status_code == 200:
        return r.json()
    else:
        return None


def ticket_as_payload(json):
    return ShowtimeTicket(price=json['price'], type_=json['type'], sku=json['sku'])


def create_showtime_from_json(data):
    if data is not None:
        showtime = Showtime()

        showtime.id_ = data['id']
        showtime.run_time = data['runTime']
        showtime.internal_release_number = data['internalReleaseNumber']
        showtime.performance_number = data['performanceNumber']
        showtime.is_sold_out = data['isSoldOut']
        showtime.movie_id = data['movieId']
        showtime.movie_name = data['movieName']
        showtime.show_date_time_local = data['showDateTimeLocal']
        showtime.show_date_time_utc = data['showDateTimeUtc']

        ticket_prices_list = []
        for ticket_data in data['ticketPrices']:
            ticket = ticket_as_payload(ticket_data)
            ticket_prices_list.append(ticket)
        showtime.ticket_prices = ticket_prices_list

        return showtime
    else:
        return None


def create_showtimes(theatre_id, date, movie_name):
    data = get_json_showtimes_at_theatre_on_date_for_movie(theatre_id, date, movie_name)

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
        print("Data not valid")

        return None


def get_showtime():
    showtime = ShowtimeTask('mperdue')
    showtime.get_city()
    showtime.get_state()
    showtime.get_title()

    # print(showtime)

    if showtime.is_valid():
        showtimes = create_showtimes(AMC_METREON_16, "09-21-2015", showtime.title)

        showtimes.print_showtimes()
    else:
        print("showtime request looks bad")


def return_json_from_file(filepath):
    data = None

    try:
        with open(filepath, "r") as myfile:
            data = json.load(myfile)
    except IOError:
        logger.error("Unable to find file")
        print("Unable to find file")

    if data:
        return data
    else:
        return None


def main():
    data = return_json_from_file("specre.json")

    # Create an empty movie object
    movie = MovieObject()

    # Populate the object with json data
    movie.populate_from_json(data)

    print(movie)

    get_showtime()


if __name__ == "__main__":
    main()
