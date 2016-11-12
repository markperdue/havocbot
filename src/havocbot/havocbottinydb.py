import logging
from tinydb import TinyDB, Query
from havocbot.user import User

logger = logging.getLogger(__name__)


class StasherTinyDB(object):
    def __init__(self):
        self.db = TinyDB('stasher/havocbot.json', default_table='users', sort_keys=True, indent=2)

    def add_user(self, user):
        pass

    def del_user(self, user):
        pass

    def find_user_by_id(self, search_user_id):
        user = None

        result = self.db.get(eid=search_user_id)

        if result is not None:
            user = self.build_user(result)

        logger.info("Returning with '%s'" % (result))

        return user

    def find_users_by_username(self, search_username):
        pass

    def find_users_by_name(self, search_name):
        pass

    def find_users_by_alias(self, search_alias):
        pass

    def build_user(self, result_data):
        user = User(result_data.eid)

        user.name = result_data['name']
        user.usernames = result_data['usernames']
        user.points = result_data['points']
        user.permissions = result_data['permissions']
        user.aliases = result_data['aliases']

        return user

