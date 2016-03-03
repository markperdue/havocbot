from havocbot.stasher import Stasher
import logging

logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, name, username):
        self.user_id = None
        self.name = name
        self.username = username
        self.aliases = []
        self.email = None
        self.points = 0
        self.plugin_data = {}

    def __str__(self):
        return "User(Name: '%s', Username: '%s', Aliases: %s, Points: %d)" % (self.name, self.username, self.get_aliases_as_string(), self.points)

    def pprint(self):
        if self.get_aliases_as_string() is not None:
            return "%s (%s) has aliases '%s' and %d points" % (self.name, self.username, self.get_aliases_as_string(), self.points)
        else:
            return "%s (%s) has %d points" % (self.name, self.username, self.points)

    def to_json(self):
        json = {
            'name': self.name,
            'username': self.username,
            'aliases': self.aliases,
            'points': self.points,
            'plugin_data': self.plugin_data
        }

        return json

    def get_aliases_as_string(self):
        if self.aliases is not None and len(self.aliases) > 0:
            return '\', \''.join(self.aliases)
        else:
            return None

    def get_plugin_data_strings_as_list(self):
        results = []

        if self.plugin_data is not None:
            for (key, value) in self.plugin_data.items():
                results.append("  %s: %s" % (key, ', '.join(['%s=%s' % (key, value) for (key, value) in value.items()])))

        return results

    def print_plugin_data(self):
        if self.plugin_data is not None:
            for (key, value) in self.plugin_data.items():
                logger.info("%s: %s" % (key, value))


class UserStash(Stasher):
    def get_user(self, search_user):
        user = None
        if self.data is not None:
            if 'users' in self.data:
                logger.info(self.data['users'])
                user_temp = next((obj for obj in self.data['users'] if search_user == obj['username'] or search_user in obj['aliases']), None)
                if user_temp is not None:
                    logger.info("user_temp is not None")
                    logger.info(user_temp)
                    user = create_user_from_json(user_temp)

        logger.info("StasherQuote.get_user() returning with '%s'" % (user))
        return user

    def add_user(self, name, username):
        if self.data is not None:
            if 'users' in self.data:
                user_temp = next((obj for obj in self.data['users'] if username == obj['username']), None)
                if user_temp is None:
                    logger.info("Adding new user")
                    # Create a new user since the user was not found
                    new_user = User(name, username)
                    self.data['users'].append(new_user.to_json())
                    self.write_db()
                    return True
                else:
                    logger.error("That user already exists")
                    return False


def create_user_from_json(json):
    user = User(json['name'], json['username'])
    user.aliases = json['aliases'] if 'aliases' in json else None
    user.points = json['points'] if 'points' in json and isinstance(json['points'], (int, long)) else None
    user.plugin_data = json['plugin_data'] if 'plugin_data' in json and isinstance(json['plugin_data'], dict) else None

    return user
