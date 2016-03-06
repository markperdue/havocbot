import json
import jsonpickle
import logging
import os
import havocbot.exceptions as exceptions
from havocbot.singletonmixin import Singleton
import havocbot.user as user

logger = logging.getLogger(__name__)


class Stasher(Singleton):
    def __init__(self):
        self.filename = 'stasher.json'
        self.data = self.load_db()

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

    def add_json_to_key(self, json, key, unique_root_key, unique_root_value):
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
                    self.data[key].append(json)
                    logger.info(self.data[key])
                    self.write_db()
            else:
                logger.info("Adding new key %s" % (key))
                self.data[key] = []
                self.data[key].append(json)
                self.write_db()

    def write_data(self):
        logger.info('Writing data')

    def add_user(self, user_object):
        logger.info(
            "Add user triggered with user_object '%s'" % (user_object)
        )
        user_json = json.loads(
            jsonpickle.encode(user_object, unpicklable=False)
        )
        logger.info("pickled user is '%s'" % (user_json))

        try:
            self.add_json_to_key(
                user_json, 'users', 'user_id', user_object.user_id
            )
        except:
            raise

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

    def get_user_by_id(self, user_id):
        result = None

        if self.data is not None:
            if 'users' in self.data:
                users = self.data['users']
                matched_users = [
                    x for x in users
                    if (
                        'user_id' in x
                        and x['user_id'] is not None
                        and x['user_id'].lower() == user_id.lower()
                    )
                ]

                if matched_users:
                    for user_json in matched_users:
                        a_user = user.user_object_from_stasher_json(user_json)
                        if a_user.is_valid():
                            logger.debug("Found user object - %s" % (a_user))
                            result = a_user

        logger.debug("get_users_by_id returning with '%s'" % (result))
        return result

    def get_users_by_name(self, name):
        results = []

        if self.data is not None:
            if 'users' in self.data:
                users = self.data['users']
                matched_users = [
                    x for x in users
                    if (
                        'username' in x
                        and x['username'] is not None
                        and x['username'].lower() == name.lower()
                    )
                    or (
                        'name' in x
                        and x['name'] is not None
                        and x['name'].lower() == name.lower()
                    )
                    or (
                        'aliases' in x
                        and x['aliases']
                        and name.lower() in x['aliases']
                    )
                ]
                if matched_users:
                    for user_json in matched_users:
                        a_user = user.user_object_from_stasher_json(user_json)
                        if a_user.is_valid():
                            logger.debug("Found user object - %s" % (a_user))
                            results.append(a_user)

        logger.debug("get_users_by_name returning with '%s'" % (results))
        return results

    def get_users(self):
        results = []

        if self.data is not None:
            if 'users' in self.data:
                for user_object in self.data['users']:
                    results.append(user_object)

        return results

    def get_aliases_for_username(self, username):
        results = []

        if self.data is not None:
            if 'user_aliases' in self.data:
                for user_alias in self.data['user_aliases']:
                    if user_alias['username'] == username:
                        logger.debug("Found alias %s for %s"
                                     % (user_alias['alias'],
                                        user_alias['username']))
                        results.append(user_alias)

        return results

    def display_aliases_for_username(self, username):
        aliases = self.get_aliases_for_username(username)
        if len(aliases) > 0:
            logger.debug("There are %d known aliases for %s"
                         % (len(aliases), username))
            for alias in aliases:
                logger.debug(alias)
        else:
            logger.debug("There are no known aliases for %s" % (username))

    def display_users(self):
        users = self.get_users()
        if len(users) > 0:
            logger.debug("There are %d known users" % (len(users)))
            for user_object in users:
                logger.debug(user_object)
        else:
            logger.debug("There are no known users")
