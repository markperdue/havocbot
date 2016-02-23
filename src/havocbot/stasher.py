import json
import jsonpickle
import logging
import os
from havocbot.singletonmixin import Singleton
import havocbot.user

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
                # data = json.load(data_file)
                data = jsonpickle.decode(json.dumps(json.load(data_file)))
            except ValueError as e:
                logger.debug(e)
                pass

        return data

    def write_db(self):
        logger.info("Writing to db")
        with open(self.filename, 'wt') as outfile:
            json.dump(json.loads(jsonpickle.encode(self.data, unpicklable=False)), outfile, indent=2, sort_keys=True)  # Rip out object references
        self.load_db()

    def add_alias(self, username, alias):
        # logger.debug("Add alias triggered with username '%s' and alias '%s'" % (username, alias))
        if self.data is not None:
            if 'user_aliases' in self.data:
                if any((user_aliases['username'] == username and user_aliases['alias'] == alias) for user_aliases in self.data['user_aliases']):
                    logger.info("Username %s already contains alias %s" % (username, alias))
                else:
                    logger.debug("Adding alias")
                    self.data['user_aliases'].append({'username': username, 'alias': alias})
                    self.write_db()
            else:
                logger.debug("Adding initial alias")
                self.data['user_aliases'] = [{'username': username, 'alias': alias}]
                self.write_db()
        else:
            self.data['user_aliases'] = [{'username': username, 'alias': alias}]
            self.write_db()

    def add_user(self, username, name):
        # logger.debug("Add user triggered with username '%s' and name '%s'" % (username, name))
        if self.data is not None:
            if 'users' in self.data:
                if any(user_object.username == username for user_object in self.data['users']):
                    logger.info("Username %s already exists" % (username))
                else:
                    logger.debug("Adding user")
                    self.data['users'].append(havocbot.user.User(name, username))
                    self.write_db()
            else:
                logger.debug("Adding initial user")
                self.data['users'] = [havocbot.user.User(name, username)]
                self.write_db()
        else:
            self.data['users'] = [havocbot.user.User(name, username)]
            self.write_db()

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
                        # logger.debug("Found alias %s for %s" % (user_alias['alias'], user_alias['username']))
                        results.append(user_alias)

        return results

    def display_aliases_for_username(self, username):
        aliases = self.get_aliases_for_username(username)
        if len(aliases) > 0:
            logger.debug("There are %d known aliases for %s" % (len(aliases), username))
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
