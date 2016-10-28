from dateutil import tz
from datetime import datetime
from havocbot.stasher import Stasher
import logging

logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, user_id):
        timestamp = (
            datetime.utcnow()
            .replace(tzinfo=tz.tzutc())
            .isoformat()
        )

        self.aliases = []
        self.is_stashed = False
        self.last_modified = timestamp
        self.name = None
        self.plugin_data = {}
        self.points = 0
        self.timestamp = timestamp
        self.user_id = user_id
        self.usernames = {}
        self.current_username = None
        self.permissions = None

    def __repr__(self):
        return ("User(%s, %s, %s, %s, %d, %s, %s)"
                % (self.name, self.aliases,
                   self.plugin_data, self.is_stashed,
                   self.points, self.timestamp, self.last_modified))

    def __str__(self):
        sb = ("User(User ID: '%d', Name: '%s', "
                    "Username %s, "
                    "Points: %d, Is Stashed: %s"
                    % (self.user_id, self.name,
                       self.current_username,
                       self.points, self.is_stashed))
        if self.aliases:
            sb += ", Aliases: %s" % (self.get_aliases_as_string())
        if self.permissions:
            sb += ", Permissions: %s" % (self.get_permissions_as_string())
        sb += ")"

        return sb

        # if self.aliases:
        #     return ("User(User ID: '%s', Name: '%s', Aliases: %s, "
        #             "Username %s, "
        #             "Points: %d, Is Stashed: %s)"
        #             % (self.user_id, self.name, self.get_aliases_as_string(),
        #                self.current_username,
        #                self.points, self.is_stashed))
        # else:
        #     return ("User(User ID: '%d', Name: '%s', "
        #             "Username %s, "
        #             "Points: %d, Is Stashed: %s)"
        #             % (self.user_id, self.name,
        #                self.current_username,
        #                self.points, self.is_stashed))

    def __eq__(self, other):
        return (isinstance(other, User) and self.user_id == other.user_id)

    def __hash__(self):
        return hash((self.user_id))

    def get_user_info_as_list(self):
        results = []

        results.append(self.get_user_header())

        if self.aliases is not None and self.aliases:
            results.append(self.get_user_aliases())

        if self.current_username is not None and self.current_username:
            results.append(self.get_user_client_info_current())

        if self.usernames is not None and self.usernames:
            results.append(self.get_user_client_info_other())

        if self.plugin_data is not None and self.plugin_data:
            results.extend(self.get_plugin_data())

        return results

    def get_user_header(self):
        if self.is_stashed:
            return "User %s (%d) has %d points" % (self.name, self.user_id, self.points)
        else:
            return "User %s" % (self.name)

    def get_user_aliases(self):
        if self.aliases is not None and self.aliases:
            return "    Aliases: %s" % (self.get_aliases_as_string())

    def get_user_client_info_current(self):
        if self.current_username is not None and self.current_username:
            return "    Username: %s" % (self.current_username)

    def get_user_client_info_other(self):
        other_usernames_list = self.get_other_usernames_as_list()
        if other_usernames_list is not None and other_usernames_list:
            return "    Other usernames: %s" % (', '.join(other_usernames_list))

    def get_plugin_data(self):
        if self.plugin_data is not None and self.plugin_data:
            return self.get_plugin_data_strings_as_list()

    def get_aliases_as_string(self):
        if self.aliases is not None and self.aliases:
            return ', '.join(self.aliases)
        else:
            return None

    def get_usernames_as_list(self):
        usernames_list = []

        if self.usernames is not None and self.usernames:
            for (client_name, value) in self.usernames.items():
                usernames_list.extend(value)

        return usernames_list

    def get_other_usernames_as_list(self):
        cleaned_list = []

        usernames_list = self.get_usernames_as_list()
        cleaned_list = [x for x in usernames_list if x != self.current_username]

        return cleaned_list

    def get_permissions_as_string(self):
        if self.permissions is not None and self.permissions:
            return ', '.join(self.permissions)
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

    def has_permission(self, permission):
        if self.permissions is not None and self.permissions:
            if permission in self.permissions:
                return True
            else:
                return False
        else:
            return False

    def is_valid(self):
        if self.user_id is not None and self.user_id > 0:
            return True

        return False

    def is_like_user(self, name_or_username_or_alias):
        # if self.user_id is not None and name_or_username_or_alias.lower() in self.user_id.lower():
        #     return True

        if self.name is not None and name_or_username_or_alias.lower() in self.name.lower():
            return True

        if self.username is not None and name_or_username_or_alias.lower() in self.username.lower():
            return True

        if self.aliases is not None and self.aliases:
            result = any(name_or_username_or_alias.lower() in alias.lower() for alias in self.aliases)
            if result is True:
                return True

        return False

    # def to_json(self):
    #     json = {
    #         'name': self.name,
    #         'aliases': self.aliases,
    #         'points': self.points,
    #         'plugin_data': self.plugin_data
    #     }
    #     # json = {
    #     #     'name': self.name,
    #     #     'username': self.username,
    #     #     'aliases': self.aliases,
    #     #     'points': self.points,
    #     #     'plugin_data': self.plugin_data
    #     # }

    #     return json


class ClientUser(object):
    def __init__(self, username, client):
        timestamp = (
            datetime.utcnow()
            .replace(tzinfo=tz.tzutc())
            .isoformat()
        )

        self.client = client
        self.last_modified = timestamp
        self.timestamp = timestamp
        self.username = username


def create_user(client, message):
    logger.info('create_user_from_callback_and_message() - triggered')
    a_user = User(0)
    a_user.name = message.sender
    a_user.username = message.sender
    a_user.is_stashed = False
    logger.info('create_user_from_callback_and_message() - user info is:')
    logger.info(a_user)

    logger.info('create_user_from_callback_and_message() - updating user object with client info...')
    client.update_user_object_from_message(a_user, message)
    logger.info('create_user_from_callback_and_message() - user info is:')
    logger.info(a_user)

    return a_user


def user_object_from_stasher_json(json):
    user = User(json['user_id'])

    user.aliases = json['aliases'] if 'aliases' in json else None
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
    user.usernames = (
        json['usernames']
        if 'usernames' in json and isinstance(json['usernames'], dict)
        else None
    )
    user.permissions = json['permissions'] if 'permissions' in json else None

    return user


def find_users_matching_client(search_string, client_integration_name):
    logger.debug("Searching for users matching search string '%s' on client '%s'" % (search_string, client_integration_name))

    results = []

    results.extend(get_users_by_name(search_string, client_integration_name))
    # results.extend(get_users_by_username(search_string, client_integration_name))  # EDIT101
    results.append(get_user_by_username_for_client(search_string, client_integration_name))
    results.extend(get_users_by_alias(search_string, client_integration_name))

    return results


def find_users_not_matching_client(search_string, client_integration_name):
    logger.debug("Searching for users matching search string '%s' not on client '%s'" % (search_string, client_integration_name))


def get_users_by_alias(search_string, client_integration_name):
    results = []

    stasher = Stasher.getInstance()

    if stasher.data is not None:
        if 'users' in stasher.data:
            users = stasher.data['users']
            matched_users = [
                x for x in users
                if (
                    (
                        'aliases' in x
                        and x['aliases']
                        and search_string.lower() in x['aliases']
                    )
                    and ('usernames' in x and x['usernames'] is not None and x['usernames'] and client_integration_name in x['usernames'])
                )
            ]

            if matched_users:
                for user_json in matched_users:
                    a_user = user_object_from_stasher_json(user_json)
                    if a_user.is_valid():
                        results.append(a_user)

    logger.debug("get_users_by_alias() returning with '[%s]'" % (', '.join(map(str, results))))
    return results


def get_users_by_name(search_string, client_integration_name):
    results = []

    stasher = Stasher.getInstance()

    if stasher.data is not None:
        if 'users' in stasher.data:
            users = stasher.data['users']
            matched_users = [
                x for x in users
                if (
                    (
                        'name' in x
                        and x['name'] is not None
                        and search_string.lower() in x['name'].lower()
                    )
                    and ('usernames' in x and x['usernames'] is not None and x['usernames'] and client_integration_name in x['usernames'])
                )
            ]

            if matched_users:
                for user_json in matched_users:
                    a_user = user_object_from_stasher_json(user_json)
                    if a_user.is_valid():
                        results.append(a_user)

    logger.debug("get_users_by_name() returning with '[%s]'" % (', '.join(map(str, results))))
    return results


# def get_user_by_username(username, stasher):
#     logger.debug("get_user_by_username() triggered in user.py")
#     result = None

#     if stasher.data is not None:
#         if 'users' in stasher.data:
#             users = stasher.data['users']
#             # matched_users = [
#             #     x for x in users
#             #     if (
#             #         'usernames' in x
#             #         and x['usernames'] is not None
#             #         and x['usernames'].lower() == user_id.lower()
#             #     )
#             # ]

#             logger.info("Searching for users...")
#             # matched_users = [x for x in users if ('usernames' in x and x['usernames'] is not None and x['usernames']) for item in x['usernames']]

#             matched_users = []
#             for x in users:
#                 if ('usernames' in x and x['usernames'] is not None and x['usernames']):
#                     for (key, value) in x['usernames'].items():
#                         for username_string in value:
#                             logger.info("Found username '%s' for '%s'" % (username_string, key))
#                             if username in username_string:
#                                 logger.info("MATCH of '%s' against '%s" % (username, username_string))
#                                 matched_users.append(x)
#                                 break

#             if matched_users is not None and matched_users:
#                 logger.info("Found %d matching users - %s" % (len(matched_users), matched_users))
#             logger.info("Done with searching for users")

#             if matched_users:
#                 for user_json in matched_users:
#                     a_user = user_object_from_stasher_json(user_json)
#                     if a_user.is_valid():
#                         logger.debug("Found user object - %s" % (a_user))
#                         result = a_user

#     logger.debug("get_user_by_username returning with '%s'" % (result))
#     return result


def get_user_by_username_for_client(username, client_integration_name):
    result = None

    stasher = Stasher.getInstance()

    if stasher.data is not None:
        if 'users' in stasher.data:
            users = stasher.data['users']

            logger.debug("get_user_by_username_for_client - Searching for users...")

            for x in users:
                if ('usernames' in x and x['usernames'] is not None and x['usernames']):
                    for (key, value) in x['usernames'].items():
                        if key == client_integration_name:
                            for username_string in value:
                                if username == username_string:
                                    result = user_object_from_stasher_json(x)
                                    result.current_username = username
                                    logger.debug("get_user_by_username_for_client - returning with '%s'" % (result))

                                    return result

    return None

# # EDIT101
# def get_users_by_username(search_string, client_integration_name):
#     results = []

#     stasher = Stasher.getInstance()

#     if stasher.data is not None:
#         if 'users' in stasher.data:
#             users = stasher.data['users']

#             matched_users = []
#             for x in users:
#                 if ('usernames' in x and x['usernames'] is not None and x['usernames']):
#                     for (key, value) in x['usernames'].items():
#                         if key == client_integration_name:
#                             for username_string in value:
#                                 if search_string in username_string:
#                                     logger.debug("MATCH of '%s' against '%s" % (search_string, username_string))
#                                     matched_users.append(x)
#                                     break

#             if matched_users:
#                 for user_json in matched_users:
#                     a_user = user_object_from_stasher_json(user_json)
#                     if a_user.is_valid():
#                         results.append(a_user)

#     logger.debug("get_users_by_username() returning with '[%s]'" % (', '.join(map(str, results))))

#     return results


def get_user_by_id(user_id, stasher):
    result = None

    if stasher.data is not None:
        if 'users' in stasher.data:
            users = stasher.data['users']
            matched_users = [
                x for x in users
                if (
                    'user_id' in x
                    and x['user_id'] is not None
                    and x['user_id'] == user_id
                )
            ]

            if matched_users:
                for user_json in matched_users:
                    a_user = user_object_from_stasher_json(user_json)
                    if a_user.is_valid():
                        logger.debug("Found user object - %s" % (a_user))
                        result = a_user

    logger.debug("get_users_by_id returning with '%s'" % (result))
    return result


def get_users(stasher):
    results = []

    if stasher.data is not None:
        if 'users' in stasher.data:
            for user_object in stasher.data['users']:
                results.append(user_object)

    return results


def get_aliases_for_username(username, stasher):
    results = []

    if stasher.data is not None:
        if 'user_aliases' in stasher.data:
            for user_alias in stasher.data['user_aliases']:
                if user_alias['username'] == username:
                    logger.debug("Found alias %s for %s"
                                 % (user_alias['alias'],
                                    user_alias['username']))
                    results.append(user_alias)

    return results


def display_aliases_for_username(username, stasher):
    aliases = stasher.get_aliases_for_username(username)
    if aliases:
        logger.debug("There are %d known aliases for %s"
                     % (len(aliases), username))
        for alias in aliases:
            logger.debug(alias)
    else:
        logger.debug("There are no known aliases for %s" % (username))


def display_users(stasher):
    users = stasher.get_users()
    if users:
        logger.debug("There are %d known users" % (len(users)))
        for user_object in users:
            logger.debug(user_object)
    else:
        logger.debug("There are no known users")


# def find_user_by_id_or_name(user_id_or_name, client, callback):
#     logger.debug("Searching for user matching user id or name '%s'" % (user_id_or_name))

#     # LOCAL FIRST
#     stasher = Stasher.getInstance()

#     # Look in stasher users to see if user_id_or_name matches a username
#     user_result = get_user_by_username(user_id_or_name, stasher)
#     if user_result is not None and user_result:
#         return user_result

#     # # Look in stasher users to see if user_id_or_name matches a name
#     # user_results = get_users_by_name(user_id_or_name, client, stasher)
#     # if user_results is not None and user_results:
#     #     # TODO - Fix this. It is returning first result for now
#     #     return user_results[0]

#     # CLIENT SECOND
#     # Look in client users to see if user_id_or_name matches a user_id
#     user_result = callback.get_user_by_id(user_id_or_name)
#     if user_result is not None and user_result:
#         return user_result

#     return None


# def find_user_by_id_or_name(user_id_or_name, client, callback):
#     logger.debug("Searching for user matching user id or name '%s'" % (user_id_or_name))

#     # LOCAL FIRST
#     stasher = Stasher.getInstance()

#     # Look in stasher users to see if user_id_or_name matches a username
#     user_result = get_user_by_username(user_id_or_name, stasher)
#     if user_result is not None and user_result:
#         return user_result

#     # # Look in stasher users to see if user_id_or_name matches a username
#     # user_result = stasher.get_user_by_username(user_id_or_name)
#     # if user_result is not None and user_result:
#     #     return user_result

#     # Look in stasher users to see if user_id_or_name matches a user_id
#     user_result = stasher.get_user_by_id(user_id_or_name)
#     if user_result is not None and user_result:
#         return user_result

#     # Look in stasher users to see if user_id_or_name matches a name
#     user_results = stasher.get_users_by_name(user_id_or_name, client)
#     if user_results is not None and user_results:
#         # TODO - Fix this. It is returning first result for now
#         return user_results[0]

#     # Look in stasher users to see if user_id_or_name matches an alias
#     # TODO - get_user_by_aliases
#     user_results = stasher.get_users_by_name(user_id_or_name, client)
#     if user_results is not None and user_results:
#         # TODO - Fix this. It is returning first result for now
#         return user_results[0]

#     # CLIENT SECOND
#     # Look in client users to see if user_id_or_name matches a user_id
#     user_result = callback.get_user_by_id(user_id_or_name)
#     if user_result is not None and user_result:
#         return user_result

#     return None


# def find_user_by_id(user_id, callback):
#     logger.debug("Searching for user matching user id '%s'" % (user_id))

#     # LOCAL FIRST
#     stasher = Stasher.getInstance()

#     # Look in stasher users to see if user_id_or_name matches a user_id
#     user_result = stasher.get_user_by_id(user_id)
#     if user_result is not None and user_result:
#         return user_result

#     # CLIENT SECOND
#     # Look in callback users to see if user_id_or_name matches a user_id
#     user_result = callback.get_user_by_id(user_id)
#     if user_result is not None and user_result:
#         return user_result

#     return None


# def find_users_by_name(name, client):
#     logger.debug("Searching for user matching name '%s'" % (name))

#     results = []

#     # LOCAL FIRST
#     stasher = Stasher.getInstance()

#     # Look in stasher users to see if user_id_or_name matches a name
#     user_results = stasher.get_users_by_name(name, client)
#     if user_results is not None and user_results:
#         results.extend(user_results)

#     return results
