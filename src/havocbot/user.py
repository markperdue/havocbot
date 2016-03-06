from dateutil import tz
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, user_id):
        self.aliases = []
        self.client = None
        self.email = None
        self.is_stashed = False
        self.last_modified = (
            datetime.utcnow()
                    .replace(tzinfo=tz.tzutc())
                    .isoformat()
        )
        self.name = None
        self.plugin_data = {}
        self.points = 0
        self.timestamp = (
            datetime.utcnow()
                    .replace(tzinfo=tz.tzutc())
                    .isoformat()
        )
        self.user_id = user_id
        self.username = None

    def __repr__(self):
        return ("User(%s, %s, %s, %s, %s, %s, %s, %s, %d, %s, %s)"
                % (self.user_id, self.name, self.username, self.aliases,
                   self.email, self.client, self.plugin_data, self.is_stashed,
                   self.points, self.timestamp, self.last_modified))

    def __str__(self):
        if self.aliases:
            return ("User(User ID: '%s', Name: '%s', Aliases: %s,"
                    "Points: %d, Is Stashed: %s)"
                    % (self.user_id, self.name, self.get_aliases_as_string(),
                       self.points, self.is_stashed))
        else:
            return ("User(User ID: '%s', Name: '%s',"
                    "Points: %d, Is Stashed: %s)"
                    % (self.user_id, self.name,
                       self.points, self.is_stashed))

    def __eq__(self, other):
        return (isinstance(other, User) and self.user_id == other.user_id)

    def __hash__(self):
        return hash((self.user_id))

    def pprint(self):
        if self.is_stashed:
            if self.aliases:
                return ("User %s (%s) has aliases '%s' and %d points"
                        % (self.name, self.user_id,
                           self.get_aliases_as_string(), self.points))
            else:
                return ("User %s (%s) has %d points"
                        % (self.name, self.user_id, self.points))
        else:
            return "Untracked user %s (%s)" % (self.name, self.user_id)

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
        if self.aliases is not None and self.aliases:
            return '\', \''.join(self.aliases)
        else:
            return None

    def get_plugin_data_strings_as_list(self):
        results = []

        if self.plugin_data is not None:
            for (plugin_name, value) in self.plugin_data.items():
                nested_kv_list = [
                    "%s=%s" % (key, value)
                    for (key, value)
                    in value.items()
                ]
                nested_kv_as_string = ', '.join(nested_kv_list)
                results.append(
                    "    %s: %s" % (plugin_name, nested_kv_as_string)
                )

        return results

    def print_plugin_data(self):
        if self.plugin_data is not None:
            for (key, value) in self.plugin_data.items():
                logger.info("%s: %s" % (key, value))

    def is_valid(self):
        if self.user_id is not None and len(self.user_id) > 0:
            return True

        return False


def user_object_from_stasher_json(json):
    user = User(json['user_id'])

    user.aliases = json['aliases'] if 'aliases' in json else None
    user.client = json['client'] if 'client' in json else None
    user.email = json['email'] if 'email' in json else None
    user.is_stashed = True
    user.last_modified = (
        json['last_modified']
        if 'last_modified'in json
        else None
    )
    user.name = json['name'] if 'name' in json else None
    user.plugin_data = (
        json['plugin_data']
        if 'plugin_data' in json and isinstance(json['plugin_data'], dict)
        else None
    )
    user.points = (
        json['points']
        if 'points' in json and isinstance(json['points'], (int, long))
        else 0
    )
    user.timestamp = json['timestamp'] if 'timestamp' in json else None
    user.username = json['username'] if 'username' in json else None

    return user
