import json
import jsonpickle
import logging
import os
import havocbot.exceptions as exceptions
from havocbot.singletonmixin import Singleton
from havocbot.user import User, StasherClass

logger = logging.getLogger(__name__)


class Stasher(Singleton):
    def __init__(self):
        self.filename = 'stasher.json'
        self.data = self.load_db()
        self.plugin_data = None

    def load_db(self):
        logger.info("Reloading from db")
        if not os.path.exists(self.filename):
            logger.info("Creating new Stasher database file")
            file(self.filename, 'wt').close()

        data = {}
        with open(self.filename, 'r+') as data_file:
            try:
                data = jsonpickle.decode(json.dumps(json.load(data_file)))
            except ValueError as e:
                logger.debug(e)
                pass

        return data

    def debug_data(self):
        logger.info('Data is:')
        logger.info(json.dumps(self.data, sort_keys=True, indent=2))
        logger.info(
            "There are %d users in the db" % (len(self.data['users']))
        )

    def write_db(self):
        logger.info("Writing to db")
        with open(self.filename, 'wt') as outfile:
            json.dump(json.loads(
                jsonpickle.encode(self.data, unpicklable=False)),
                outfile, indent=2, sort_keys=True)
        self.load_db()

    def add_json_to_key(self, json_data, key, unique_root_key, unique_root_value):
        if self.data is not None:
            if key in self.data:
                logger.info("Key '%s' is known" % (key))
                result = next((
                    x for x in self.data[key]
                    if unique_root_key in x
                       and x[unique_root_key] == unique_root_value
                ), None)
                if result is not None:
                    logger.error("Match found for record. Not unique")
                    logger.error("%s" % (result))
                    raise exceptions.StasherEntryAlreadyExistsError(result)
                else:
                    logger.info("No match found for record. Unique entry")
                    self.data[key].append(json_data)
                    logger.info(self.data[key])
                    self.write_db()
            else:
                logger.info("Adding new key %s" % (key))
                self.data[key] = []
                self.data[key].append(json_data)
                self.write_db()

    def update_json_for_key(self, json_data, key, unique_root_key, unique_root_value):
        if self.data is not None:
            if key in self.data:
                logger.info("Key '%s' is known" % (key))
                result = next((
                    x for x in self.data[key]
                    if unique_root_key in x
                       and x[unique_root_key] == unique_root_value
                ), None)

                if result is not None:
                    result = json_data
            else:
                logger.info("Adding new key %s" % (key))
                self.data[key] = []
                self.data[key].append(json_data)

            self.write_db()

    def write_data(self):
        logger.info('Writing data')

    def add_user(self, user_object):
        logger.info("Add user triggered with user_object '%s'" % (user_object))
        user_json = json.loads(jsonpickle.encode(user_object, unpicklable=False))
        logger.info("pickled user is '%s'" % (user_json))

        try:
            self.add_json_to_key(user_json, 'users', 'user_id', user_object.user_id)
        except:
            raise

    def update_user(self, user_object):
        logger.info("Update user triggered with user_object '%s'" % (user_object))
        user_json = json.loads(jsonpickle.encode(user_object, unpicklable=False))
        logger.info("pickled user is '%s'" % (user_json))

        try:
            self.update_json_for_key(user_json, 'users', 'user_id', user_object.user_id)
        except:
            raise

    def add_or_update_user(self, user_object):
        result = next((x for x in self.data['users'] if 'user_id' in x and x['user_id'] == user_object.user_id), None)

        if result is not None:
            self.update_user(user_object)
        else:
            self.add_user(user_object)

    def add_alias(self, username, alias):
        # logger.debug("Add alias triggered with username '%s' and alias '%s'"
        #              % (username, alias))
        if self.data is not None:
            if 'user_aliases' in self.data:
                if any((user_aliases['username'] == username
                        and user_aliases['alias'] == alias)
                       for user_aliases in self.data['user_aliases']):
                    logger.info("Username %s already contains alias %s"
                                % (username, alias))
                else:
                    logger.debug("Adding alias")
                    self.data['user_aliases'].append(
                        {'username': username, 'alias': alias})
                    self.write_db()
            else:
                logger.debug("Adding initial alias")
                self.data['user_aliases'] = [
                    {'username': username, 'alias': alias}
                ]
                self.write_db()
        else:
            self.data['user_aliases'] = [
                {'username': username, 'alias': alias}
            ]
            self.write_db()

    # def get_user_by_id(self, user_id):
    #     result = None
    #
    #     if self.data is not None:
    #         if 'users' in self.data:
    #             users = self.data['users']
    #             matched_users = [
    #                 x for x in users
    #                 if (
    #                     'user_id' in x
    #                     and x['user_id'] is not None
    #                     and x['user_id'] == user_id
    #                 )
    #             ]
    #
    #             if matched_users:
    #                 for user_json in matched_users:
    #                     a_user = havocbot.user.user_object_from_stasher_json(user_json)
    #                     if a_user.is_valid():
    #                         logger.debug("Found user object - %s" % (a_user))
    #                         result = a_user
    #
    #     logger.debug("get_users_by_id returning with '%s'" % (result))
    #     return result

    def get_plugin_data(self, plugin_name):
        data = {}

        plugin_file = "stasher/%s.json" % (plugin_name)

        with open(plugin_file) as data_file:
            try:
                data = jsonpickle.decode(json.dumps(json.load(data_file)))
            except ValueError as e:
                logger.debug(e)
                pass

        return data

    # def add_points(self, user_id, points):
    #     if isinstance(points, (int, long)):
    #
    #         stashed_user = havocbot.user.get_user_by_id(user_id)
    #         if stashed_user is not None and stashed_user:
    #             logger.info("Users existing points set to %d. Adding %d points" % (stashed_user.points, points))
    #
    #             if isinstance(stashed_user.points, (int, long)):
    #                 logger.debug("Users existing points set to %d. Adding %d points" % (stashed_user.points, points))
    #                 stashed_user.points += points
    #                 # self.write_db()
    #             else:
    #                 logger.debug("Adding initial points of %d" % (points))
    #                 stashed_user.points = points
    #                 # self.write_db()
    #     else:
    #         logger.error('Points must be an integer')

    # def subtract_points(self, user_id, points):
    #     if isinstance(points, (int, long)):
    #         if self.data is not None:
    #             if 'points' in self.data:
    #                 logger.debug("Users existing points set to %d. Subtracting %d points" % (self.data['points'], points))
    #                 self.data['points'] -= points
    #                 self.write_db()
    #             else:
    #                 logger.debug("Adding initial points of %d" % (points))
    #                 self.data['points'] = points * -1
    #                 self.write_db()
    #     else:
    #         logger.error('Points must be an integer')

    def write_plugin_data(self, plugin_name):
        plugin_file = "stasher/%s.json" % (plugin_name)

        logger.info("Writing plugin data to '%s'" % (plugin_file))
        logger.info(self.plugin_data)

        with open(plugin_file, 'wt') as outfile:
            json.dump(json.loads(
                jsonpickle.encode(self.plugin_data, unpicklable=False)),
                outfile, indent=2, sort_keys=True)
        self.plugin_data = self.get_plugin_data(plugin_name)


class StasherDB(StasherClass):
    def __init__(self):
        self.stasher = Stasher.getInstance()
        self.db = self.stasher.data

    def add_user(self, user):
        pass

    def del_user(self, user):
        pass

    def add_alias_to_user_id(self, user_id, alias):
        pass

    def del_alias_to_user_id(self, user_id, alias):
        pass

    def add_permission_to_user_id(self, user_id, permission):
        pass

    def del_permission_to_user_id(self, user_id, permission):
        pass

    def add_points_to_user_id(self, user_id, points):
        if isinstance(points, (int, long)):

            stashed_user = self.find_user_by_id(user_id)
            if stashed_user is not None and stashed_user:
                logger.info("Users existing points set to %d. Adding %d points" % (stashed_user.points, points))

                if isinstance(stashed_user.points, (int, long)):
                    logger.debug("Users existing points set to %d. Adding %d points" % (stashed_user.points, points))
                    stashed_user.points += points
                    # self.write_db()
                else:
                    logger.debug("Adding initial points of %d" % (points))
                    stashed_user.points = points
                    # self.write_db()
        else:
            logger.error('Points must be an integer')

    def del_points_to_user_id(self, user_id, points):
        if isinstance(points, (int, long)):

            stashed_user = self.find_user_by_id(user_id)
            if stashed_user is not None and stashed_user:
                logger.info("Users existing points set to %d. Subtracting %d points" % (stashed_user.points, points))

                if isinstance(stashed_user.points, (int, long)):
                    logger.debug(
                        "Users existing points set to %d. Subtracting %d points" % (stashed_user.points, points))
                    stashed_user.points -= points
                    # self.write_db()
                else:
                    logger.debug("Adding initial points of %d" % (points))
                    stashed_user.points = -points
                    # self.write_db()
        else:
            logger.error('Points must be an integer')

    def find_user_by_id(self, search_user_id):
        result = None

        if self.db is not None and 'users' in self.db:
            user_data = self.db['users']

            match = next(
                (x for x in user_data if
                 'user_id' in x and x['user_id'] is not None and x['user_id'] == int(search_user_id)),
                None)

            if match:
                logger.debug(match)
                a_user = self.build_user(match)
                if a_user.is_valid():
                    logger.debug("Found user object - %s" % (a_user))
                    result = a_user

        logger.debug("find_user_by_id returning with '%s'" % (result))
        return result

    def find_user_by_username_for_client(self, search_username, client_name):
        result = None

        if self.db is not None:
            if 'users' in self.db:
                users = self.db['users']

                logger.debug("find_user_by_username_for_client - Searching for users...")

                for x in users:
                    if 'usernames' in x and x['usernames'] is not None and x['usernames']:
                        for (key, value) in x['usernames'].items():
                            if key == client_name:
                                for username_string in value:
                                    if search_username == username_string:
                                        result = self.build_user(x)
                                        result.current_username = search_username
                                        logger.debug(
                                            "find_user_by_username_for_client - returning with '%s'" % (result))

                                        return result

        return None

    def find_users_by_username(self, search_username):
        pass

    def find_users_by_name_for_client(self, search_name, client_name):
        results = []

        if self.db is not None:
            if 'users' in self.db:
                users = self.db['users']
                matched_users = [
                    x for x in users
                    if (
                        ('name' in x and x['name'] is not None
                         and search_name.lower() in x['name'].lower())
                        and
                        ('usernames' in x and x['usernames'] is not None
                         and x['usernames'] and client_name in x['usernames']
                         )
                    )
                ]

                if matched_users:
                    for user_json in matched_users:
                        a_user = self.build_user(user_json)
                        if a_user.is_valid():
                            results.append(a_user)

        logger.debug("find_users_by_name - returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_alias_for_client(self, search_alias, client_name):
        results = []

        if self.db is not None:
            if 'users' in self.db:
                users = self.db['users']
                matched_users = [
                    x for x in users
                    if (
                        (
                            'aliases' in x
                            and x['aliases']
                            and search_alias.lower() in x['aliases']
                        )
                        and ('usernames' in x and x['usernames'] is not None and x[
                            'usernames'] and client_name in x['usernames'])
                    )
                ]

                if matched_users:
                    for user_json in matched_users:
                        a_user = self.build_user(user_json)
                        if a_user.is_valid():
                            results.append(a_user)

        logger.debug("get_users_by_alias() returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_matching_string_for_client(self, search_string, client_name):
        results = []

        logger.debug("Searching for users matching string '%s' on client '%s'" % (search_string, client_name))
        results.extend(self.find_users_by_name_for_client(search_string, client_name))
        user_result = self.find_user_by_username_for_client(search_string, client_name)
        if user_result is not None and user_result:
            results.append(user_result)

        results.extend(self.find_users_by_alias_for_client(search_string, client_name))
        # results.extend(get_users_by_username(search_string, client_integration_name))  # EDIT101

        return results

    def find_all_users(self):
        pass

    def build_user(self, result_data):
        user = User(result_data['user_id'])

        user.aliases = result_data['aliases'] if 'aliases' in result_data else None
        user.is_stashed = True
        user.last_modified = (
            result_data['last_modified']
            if 'last_modified' in result_data
            else None
        )
        user.name = result_data['name'] if 'name' in result_data else None
        user.plugin_data = (
            result_data['plugin_data']
            if 'plugin_data' in result_data and isinstance(result_data['plugin_data'], dict)
            else None
        )
        user.points = (
            result_data['points']
            if 'points' in result_data and isinstance(result_data['points'], (int, long))
            else 0
        )
        user.timestamp = result_data['timestamp'] if 'timestamp' in result_data else None
        user.usernames = (
            result_data['usernames']
            if 'usernames' in result_data and isinstance(result_data['usernames'], dict)
            else None
        )
        user.permissions = result_data['permissions'] if 'permissions' in result_data else None

        return user
