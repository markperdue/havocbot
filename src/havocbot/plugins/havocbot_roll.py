#!/havocbot

import logging
import random
from random import choice
import threading
import time
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.stasher import StasherDB

logger = logging.getLogger(__name__)


class RollPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "a dice roller"

    @property
    def plugin_short_name(self):
        return "roll"

    @property
    def plugin_usages(self):
        return [
            Usage(command="!roll", example=None, description="roll a 100 side dice"),
            Usage(command="!highroll", example=None, description="roll a much larger dice"),
            Usage(command="!rolloff", example=None, description="start a rolloff if one is not started or join a rolloff if one is in process"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match="!roll", function=self.start, param_dict=None, requires=None),
            Trigger(match="!highroll", function=self.high_roll, param_dict=None, requires=None),
            Trigger(match="!rolloff", function=self.rolloff, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.rolloff_join_window = 10
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = None
        self.rolloff_rollers_initial = None
        self.rolloff_minimum_players = 1
        self.should_award_points = True

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = True

        # Return true if this plugin has the information required to work
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, client, message, **kwargs):
        if message.to:
            roll_result = self.get_roll(100)

            user_object = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
            self.display_roll(client, message, user_object, roll_result)

    def high_roll(self, client, message, **kwargs):
        if message.to:
            roll_result = self.get_roll(100000000000)

            user_object = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
            self.display_roll(client, message, user_object, roll_result)

    def get_roll(self, max_roll):
        return random.SystemRandom().randrange(1, max_roll + 1)

    def display_roll(self, client, message, user_object, roll):
        roll_formatted = "{:,}".format(roll)  # Format large numbers for Americans

        if user_object is not None:
            text = "%s rolled %s" % (user_object.name, roll_formatted)
        else:
            text = "%s rolled %s" % (message.sender, roll_formatted)

        client.send_message(text, message.reply(), event=message.event)

    def rolloff(self, client, message, **kwargs):
        user_object = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)

        if user_object is not None:
            if not self.rolloff_in_process:
                # Start a new rolloff
                self.new_rolloff(client, message)

            self.add_user_to_rolloff(client, message, user_object)
        else:
            text = "Only known users can do that."
            client.send_message(text, message.reply(), event=message.event)

    def new_rolloff(self, client, message):
        text = "Time to throw it down. A %s rolloff has been called. Join the rolloff in the next %s seconds by typing '!rolloff'" % ('regular', self.rolloff_join_window)
        client.send_message(text, message.reply(), event=message.event)

        self.rolloff_enable()

        bg_thread = threading.Thread(target=self.background_thread, args=[client, message])
        bg_thread.start()

    def rolloff_enable(self):
        logger.debug("rolloff_enable() triggered")
        self.rolloff_in_process = True
        self.rolloff_start_time = time.time()
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def rolloff_disable(self):
        logger.debug("rolloff_disable() triggered")
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def add_user_to_rolloff(self, client, message, user):
        if self.rolloff_in_process:
            elapsed_time = time.time() - self.rolloff_start_time

            if 0 < elapsed_time < self.rolloff_join_window:
                logger.info("Checking on adding user '%s' to list '%s'" % (user, self.rolloff_rollers_initial))

                if any(x.current_username == user.current_username for x in self.rolloff_rollers_initial):
                    text = "You are already in this round %s" % (user.name)
                    client.send_message(text, message.reply(), event=message.event)
                else:
                    text = "Added user '%s'" % (user.name)
                    logger.debug(text)
                    self.rolloff_rollers_initial.append(user)
            else:
                text = "Entries for this round has ended"
                client.send_message(text, message.reply(), event=message.event)
        else:
            text = "There is no rolloff to join. Aww, nice try"
            client.send_message(text, message.reply(), event=message.event)

    def run_rolloff_round(self, client, message, round_participants):
        round_winners_dict = {'users': [], 'roll': 0}

        for user in round_participants:
            # Sleep to build up some drama
            time.sleep(2)

            roll_result = self.get_roll(100)
            roll_value_formatted = "{:,}".format(roll_result)  # Format large numbers for Americans

            text = "%s rolled %s" % (user.name, roll_value_formatted)
            client.send_message(text, message.reply(), event=message.event)

            if roll_result > round_winners_dict['roll']:
                round_winners_dict['users'] = [user]
                round_winners_dict['roll'] = roll_result
            elif roll_result == round_winners_dict['roll']:
                round_winners_dict['users'].append(user)
                logger.debug("<run_rolloff_round>: tied_users are '%s'" % (round_winners_dict['users']))

        if len(round_winners_dict['users']) == 1:
            logger.debug("Found a single winner")
            self.rolloff_winner_found = True
        else:
            logger.debug("No single winner found")
            tie_phrases = [
                'A tie?! This cannot be... There can be only one!',
                'What the? A tied score cannot stand. Fixing...',
                'DEALING WITH IT',
                'Everyone is out except for the people tied!'
            ]
            text = "%s" % (choice(tie_phrases))
            client.send_message(text, message.reply(), event=message.event)
            self.rolloff_winner_found = False

        return round_winners_dict

    def run_rolloff(self, client, message, initial_participants):
        # Create a copy of the original list
        round_participants = list(initial_participants)

        if len(initial_participants) >= self.rolloff_minimum_players:
            winners = None

            self.rolloff_winner_found = False
            while not self.rolloff_winner_found:
                winners = self.run_rolloff_round(client, message, round_participants)

            text = "%s wins with %s" % (winners['users'][0].name, winners['roll'])
            client.send_message(text, message.reply(), event=message.event)

            if self.should_award_points:
                self.award_points(winners['users'][0], initial_participants, client, message)
        else:
            text = "Not enough players"
            client.send_message(text, message.reply(), event=message.event)

        self.rolloff_disable()

    def award_points(self, winner_user_object, initial_participants, client, message):
        logger.info('award_points() - triggered')

        logger.info('award_points() - there were %s initial participants' % (len(initial_participants)))

        stasher = StasherDB.getInstance()

        # EDIT101
        # matching_users = havocbot.user.get_users_by_username(winner_user_object.current_username, client.integration_name)
        # if matching_users is not None and matching_users:
        #     if len(matching_users) == 1:
        #         logger.info('award_points() - adding %d points to \'%s\' (id \'%s\')' % (len(initial_participants), winner_user_object.current_username, matching_users[0].user_id))
        #         stasher.add_points(matching_users[0].user_id, len(initial_participants))
        #     else:
        #         logger.info('award_points() - more than 1 user match found')
        # else:
        #     logger.info('award_points() - no stashed user found. cannot award points to winner')

        matching_user = self.havocbot.db.find_user_by_username_for_client(winner_user_object.current_username, client.integration_name)
        if matching_user is not None and matching_user:
            logger.info('award_points() - adding %d points to \'%s\' (id \'%s\')' % (len(initial_participants), winner_user_object.current_username, matching_users.user_id))
            self.havocbot.db.add_points_to_user_id(matching_users.user_id, len(initial_participants))
        else:
            logger.info('award_points() - no stashed user found. cannot award points to winner')

        for user in initial_participants:
            if winner_user_object.current_username != user.current_username:
                logger.info('award_points() - \'%s\' lost 1 point' % (user.current_username))

    def background_thread(self, client, message):
        time.sleep(self.rolloff_join_window)
        logger.debug("background_thread() - triggered")
        self.run_rolloff(client, message, self.rolloff_rollers_initial)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
