import json
import jsonpickle
import logging
import os
import havocbot.exceptions as exceptions
from havocbot.singletonmixin import Singleton
import havocbot.user

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
                        and x['user_id'] == user_id
                    )
                ]

                if matched_users:
                    for user_json in matched_users:
                        a_user = havocbot.user.user_object_from_stasher_json(user_json)
                        if a_user.is_valid():
                            logger.debug("Found user object - %s" % (a_user))
                            result = a_user

        logger.debug("get_users_by_id returning with '%s'" % (result))
        return result

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

    def add_points(self, user_id, points):
        if isinstance(points, (int, long)):
            stashed_user = self.get_user_by_id(user_id)
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

    def subtract_points(self, user_id, points):
        if isinstance(points, (int, long)):
            if self.data is not None:
                if 'points' in self.data:
                    logger.debug("Users existing points set to %d. Subtracting %d points" % (self.data['points'], points))
                    self.data['points'] -= points
                    self.write_db()
                else:
                    logger.debug("Adding initial points of %d" % (points))
                    self.data['points'] = points * -1
                    self.write_db()
        else:
            logger.error('Points must be an integer')

    def write_plugin_data(self, plugin_name):
        plugin_file = "stasher/%s.json" % (plugin_name)

        logger.info("Writing plugin data to '%s'" % (plugin_file))
        logger.info(self.plugin_data)

        with open(plugin_file, 'wt') as outfile:
            json.dump(json.loads(
                      jsonpickle.encode(self.plugin_data, unpicklable=False)),
                      outfile, indent=2, sort_keys=True)
        self.plugin_data = self.get_plugin_data(plugin_name)
