import logging
from tinydb import TinyDB, Query
from havocbot.user import (
    User, StasherClass, UserDataAlreadyExistsException, UserDataNotFoundException, UserDoesNotExist)

logger = logging.getLogger(__name__)


class StasherTinyDB(StasherClass):
    def __init__(self):
        self.db = TinyDB('stasher/havocbot.json', default_table='users', sort_keys=True, indent=2)

    def add_user(self, user):
        # Iterate through the user's usernames and see if any usernames already exist
        if self._user_exists(user):
            logger.error("This user already exists in the db")
            raise UserDataAlreadyExistsException

        logger.info("Adding new user '%s' to database" % user.name)

        logger.debug("add_user - adding '%s'" % (user.to_dict_for_db()))
        self.db.insert(user.to_dict_for_db())

    def del_user(self, user):
        pass

    def add_permission_to_user_id(self, user_id, permission):
        try:
            self._add_string_to_list_by_key_for_user_id(user_id, 'permissions', permission)
        except:
            raise

    def del_permission_to_user_id(self, user_id, permission):
        try:
            self._del_string_to_list_by_key_for_user_id(user_id, 'permissions', permission)
        except:
            raise

    def add_alias_to_user_id(self, user_id, alias):
        try:
            self._add_string_to_list_by_key_for_user_id(user_id, 'aliases', alias)
        except:
            raise

    def del_alias_to_user_id(self, user_id, alias):
        try:
            self._del_string_to_list_by_key_for_user_id(user_id, 'aliases', alias)
        except:
            raise

    def add_points_to_user_id(self, user_id, points):
        logger.info("Adding %d points to user id %s" % (points, user_id))

        def increment_by_value(field, value):
            def transform(element):
                element[field] += int(value)

            return transform

        try:
            self.db.update(increment_by_value('points', points), eids=[user_id])
        except KeyError:
            raise UserDoesNotExist

    def del_points_to_user_id(self, user_id, points):
        logger.info("Deleting %d points from user id %s" % (points, user_id))

        def decrement_by_value(field, value):
            def transform(element):
                element[field] -= int(value)

            return transform

        try:
            self.db.update(decrement_by_value('points', points), eids=[user_id])
        except KeyError:
            raise UserDoesNotExist

    def find_user_by_id(self, search_user_id):
        logger.info("Searching for '%s'" % search_user_id)

        result = self.db.get(eid=search_user_id)

        if result is not None:
            return self.build_user(result)
        else:
            raise UserDoesNotExist

    def find_user_by_username_for_client(self, search_username, client_name):
        logger.info("Searching for '%s' in client '%s'" % (search_username, client_name))

        user_query = Query()
        result_list = self.db.search(user_query.usernames[client_name].any([search_username]))

        if result_list is not None and result_list:
            if len(result_list) == 1:
                return self.build_user(result_list[0])

        raise UserDoesNotExist

    def find_users_by_username(self, search_username):
        # user_list = None
        #
        # UserQuery = Query()
        # results = self.db.search(UserQuery.usernames[client_name].any([search_username]))
        #
        # if results is not None and results:
        #     user_list = []
        #     for user in results:
        #         user_list.append(self.build_user(user))
        #     user_list = results
        #
        # return user_list
        pass

    def find_users_by_name_for_client(self, search_name, client_name):
        logger.info("Searching for '%s' in client '%s'" % (search_name, client_name))
        results = []

        def name_test_func(val, nested_search_name):
            return val.lower() == nested_search_name.lower()

        user_query = Query()
        matched_users = self.db.search((user_query['name'].test(name_test_func, search_name)) &
                                       (user_query['usernames'].any([client_name]))
                                       )

        if matched_users:
            for matched_user in matched_users:
                a_user = self.build_user(matched_user)
                if a_user.is_valid():
                    results.append(a_user)

        logger.debug("Returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_alias_for_client(self, search_alias, client_name):
        logger.info("Searching for '%s' in client '%s'" % (search_alias, client_name))
        results = []

        def alias_test_func(val, nested_search_alias):
            return any(x.lower() for x in val if x.lower() == search_alias.lower())

        user_query = Query()
        matched_users = self.db.search((user_query['aliases'].test(alias_test_func, search_alias)) &
                                       (user_query['usernames'].any([client_name]))
                                       )

        if matched_users:
            for matched_user in matched_users:
                a_user = self.build_user(matched_user)
                if a_user.is_valid():
                    results.append(a_user)

        logger.debug("Returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_matching_string_for_client(self, search_string, client_name):
        logger.info("Searching for '%s' in client '%s'" % (search_string, client_name))

        results = []

        results_name = self.find_users_by_name_for_client(search_string, client_name)
        if results_name is not None and results_name:
            results.extend(results_name)

        try:
            result_username = self.find_user_by_username_for_client(search_string, client_name)
        except UserDoesNotExist:
            pass
        else:
            results.append(result_username)

        results_alias = self.find_users_by_alias_for_client(search_string, client_name)
        if results_alias is not None and results_alias:
            results.extend(results_alias)

        return results

    def find_all_users(self):
        pass

    def set_image_for_user_id(self, user_id, url):
        logger.info("Setting %s url to user id %s" % (url, user_id))

        if url is not None and 'http' not in url:
            raise ValueError

        a_user = self.db.get(eid=user_id)

        if a_user is None:
            raise UserDoesNotExist

        self.db.update({'image': url}, eids=[user_id])

    def build_user(self, result_data):
        user = User(result_data.eid)

        user.name = result_data['name'] if 'name' in result_data else None
        user.usernames = result_data['usernames'] if 'usernames' in result_data else {}
        user.points = result_data['points'] if 'points' in result_data else None
        user.permissions = result_data['permissions'] if 'permissions' in result_data else []
        user.aliases = result_data['aliases'] if 'aliases' in result_data else []
        user.image = result_data['image'] if 'image' in result_data else None
        user.is_stashed = True

        return user

    def _add_string_to_list_by_key_for_user_id(self, user_id, list_key, string_item):
        logger.info("Adding '%s' item '%s' to user id %d" % (list_key, string_item, user_id))

        a_user = self.db.get(eid=user_id)

        if a_user is None:
            raise UserDoesNotExist

        list_items = []

        try:
            list_items = self.db.get(eid=user_id)[list_key]
        except KeyError:
            logger.info("No items found for list '%s' for user id '%d'" % (list_key, user_id))
            list_items = [string_item]
        else:
            if string_item in list_items:
                raise UserDataAlreadyExistsException
            else:
                list_items.append(string_item)
        finally:
            logger.debug("Updating '%s' to '%s' for user id '%s'" % (list_key, list_items, user_id))
            self.db.update({list_key: list_items}, eids=[user_id])

    def _del_string_to_list_by_key_for_user_id(self, user_id, list_key, string_item):
        logger.info("Deleting '%s' item '%s' from user id %d" % (list_key, string_item, user_id))

        a_user = self.db.get(eid=user_id)

        if a_user is None:
            raise UserDoesNotExist

        list_items = []

        try:
            list_items = self.db.get(eid=user_id)[list_key]
        except KeyError:
            raise
        else:
            if string_item not in list_items:
                raise UserDataNotFoundException
            else:
                list_items.remove(string_item)
                logger.debug("Updating '%s' to '%s' for user id '%s'" % (list_key, list_items, user_id))
                self.db.update({list_key: list_items}, eids=[user_id])

    def _user_exists(self, user):
        # Iterate through the user's usernames and see if any usernames already exist
        if user.usernames is not None and user.usernames:
            for (key, value) in user.usernames.items():
                logger.info("Iterating over key '%s' with value '%s'" % (key, value))
                for username in value:
                    logger.info("Iterating over username '%s'" % username)

                    try:
                        self.find_user_by_username_for_client(username, key)
                    except UserDoesNotExist:
                        return False
                    else:
                        return True

        return False
