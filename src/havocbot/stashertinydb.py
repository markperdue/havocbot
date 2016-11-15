import logging
from tinydb import TinyDB, Query
from havocbot.user import User, StasherClass

logger = logging.getLogger(__name__)


class StasherTinyDB(StasherClass):
    def __init__(self):
        self.db = TinyDB('stasher/havocbot.json', default_table='users', sort_keys=True, indent=2)

    def add_user(self, user):
        pass

    def del_user(self, user):
        pass

    def add_points_to_user_id(self, user_id, points):
        logger.debug("add_points_to_user_id - adding %d points to '%s'" % (points, user_id))

        def increment_by_value(field, value):
            def transform(element):
                element[field] += int(value)

            return transform

        self.db.update(increment_by_value('points', points), eids=[user_id])

    def del_points_to_user_id(self, user_id, points):
        logger.debug("del_points_to_user_id - deleting %d points from '%s'" % (points, user_id))

        def decrement_by_value(field, value):
            def transform(element):
                element[field] -= int(value)

            return transform

        self.db.update(decrement_by_value('points', points), eids=[user_id])

    def find_user_by_id(self, search_user_id):
        user = None

        result = self.db.get(eid=search_user_id)

        if result is not None:
            user = self.build_user(result)

        return user

    def find_user_by_username_for_client(self, search_username, client_name):
        user = None

        UserQuery = Query()
        result_list = self.db.search(UserQuery.usernames[client_name].any([search_username]))

        if result_list is not None and result_list:
            if len(result_list) == 1:
                user = self.build_user(result_list[0])

        return user

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
        results = []

        UserQuery = Query()
        matched_users = self.db.search(UserQuery.name == search_name)

        if matched_users:
            for matched_user in matched_users:
                a_user = self.build_user(matched_user)
                if a_user.is_valid():
                    results.append(a_user)

        logger.debug("find_users_by_name_for_client - returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_alias_for_client(self, search_alias, client_name):
        return None

    def find_users_by_matching_string_for_client(self, search_string, client_name):
        results = []

        logger.debug("Searching for users matching string '%s' on client '%s'" % (search_string, client_name))

        results_name = self.find_users_by_name_for_client(search_string, client_name)
        if results_name is not None and results_name:
            logger.info("Adding '%s'" % (results_name))
            results.extend(results_name)

        result_username = self.find_user_by_username_for_client(search_string, client_name)
        if result_username is not None and result_username:
            logger.info("Adding a thing")
            results.append(result_username)

        results_alias = self.find_users_by_alias_for_client(search_string, client_name)
        if results_alias is not None and results_alias:
            results.extend(results_alias)

        # results.extend(get_users_by_username(search_string, client_integration_name))  # EDIT101

        return results

    def find_all_users(self):
        pass

    def build_user(self, result_data):
        user = User(result_data.eid)

        user.name = result_data['name']
        user.usernames = result_data['usernames']
        user.points = result_data['points']
        user.permissions = result_data['permissions']
        user.aliases = result_data['aliases']
        user.is_stashed = True

        return user

