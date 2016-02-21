from havocbot.stasher import Stasher
import logging

logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, name, username):
        self.name = name
        self.username = username
        self.aliases = None
        self.points = 0
        self.plugin_data = None

    def __str__(self):
        return "User(Name: '%s', Username: '%s', Aliases: %s, Points: %d)" % (self.name, self.username, self.get_aliases_as_string(), self.points)

    def pprint(self):
        return "%s (%s) has aliases '%s' and %d points" % (self.name, self.username, self.get_aliases_as_string(), self.points)

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
                user_temp = next((obj for obj in self.data['users'] if search_user == obj['username'] or search_user in obj['aliases']), None)
                if user_temp is not None:
                    user = create_user_from_json(user_temp)

        logger.info("StasherQuote.get_user() returning with '%s'" % (user))
        return user


def create_user_from_json(json):
    user = User(json['name'], json['username'])
    user.aliases = json['aliases'] if 'aliases' in json else None
    user.points = json['points'] if 'points' in json and isinstance(json['points'], (int, long)) else None
    user.plugin_data = json['plugin_data'] if 'plugin_data' in json and isinstance(json['plugin_data'], dict) else None

    return user
