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
        pass

    def del_points_to_user_id(self, user_id, points):
        pass

    def find_user_by_id(self, search_user_id):
        user = None

        result = self.db.get(eid=search_user_id)

        if result is not None:
            user = self.build_user(result)

        logger.debug("find_user_by_id - returning with '%s'" % (user))
        return user

    def find_user_by_username_for_client(self, search_username, client_name):
        user = None

        user_query = Query()
        result_list = self.db.search(user_query.usernames[client_name].any([search_username]))

        if result_list is not None and result_list:
            if len(result_list) == 1:
                user = self.build_user(result_list[0])

        logger.debug("find_user_by_username_for_client - returning with '%s'" % (user))
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

        logger.debug("find_users_by_name_for_client - returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_alias_for_client(self, search_alias, client_name):
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

        logger.debug("find_users_by_alias_for_client - returning with '[%s]'" % (', '.join(map(str, results))))
        return results

    def find_users_by_matching_string_for_client(self, search_string, client_name):
        results = []

        logger.debug("Searching for users matching string '%s' on client '%s'" % (search_string, client_name))

        results_name = self.find_users_by_name_for_client(search_string, client_name)
        if results_name is not None and results_name:
            results.extend(results_name)

        result_username = self.find_user_by_username_for_client(search_string, client_name)
        if result_username is not None and result_username:
            results.append(result_username)

        results_alias = self.find_users_by_alias_for_client(search_string, client_name)
        if results_alias is not None and results_alias:
            results.extend(results_alias)

        return results

    def find_all_users(self):
        pass

    def build_user(self, result_data):
        user = User(result_data.eid)

        user.name = result_data['name'] if 'name' in result_data else None
        user.usernames = result_data['usernames'] if 'usernames' in result_data else {}
        user.points = result_data['points'] if 'points' in result_data else None
        user.permissions = result_data['permissions'] if 'permissions' in result_data else []
        user.aliases = result_data['aliases'] if 'aliases' in result_data else []
        user.is_stashed = True

        return user
