#!/havocbot

import logging
import random
from random import choice
import threading
import time
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

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
            Trigger(match="!highroll", function=self.trigger_high_roll, param_dict=None, requires=None),
            Trigger(match="!rolloff", function=self.trigger_rolloff, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.rolloff_join_interval = None
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = None
        self.rolloff_rollers_initial = None
        self.rolloff_minimum_players = None
        self.should_award_points = False

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = False

        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'join_interval':
                    self.rolloff_join_interval = int(item[1])
                elif item[0] == 'minimal_players':
                    self.rolloff_minimum_players = int(item[1])
                elif item[0] == 'award_points':
                    self.should_award_points = item[1]

        if self.rolloff_join_interval is not None and self.rolloff_minimum_players is not None:
            if self.rolloff_join_interval > 0 and isinstance(self.rolloff_join_interval, int):
                if self.rolloff_minimum_players > 0 and isinstance(self.rolloff_minimum_players, int):
                    requirements_met = True
                else:
                    logger.error('There was an issue with the minimal players number. Verify minimum_players is set in the settings file')
            else:
                logger.error('There was an issue with the join interval value. Verify join_interval is set in the settings file')

        # Return true if this plugin has the information required to connect
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

    def trigger_high_roll(self, client, message, **kwargs):
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

    def trigger_rolloff(self, client, message, **kwargs):
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
        start_phrases = [
            'Time to throw it down.',
            'Let\'s get this started!',
            'Here we go!',
            'Oh doggy!'
        ]
        text = "%s " % (choice(start_phrases))
        text += "A %s rolloff has been called. " % ('regular')
        if self.should_award_points:
            text += "Wager 1 point and join the rolloff in the next %s seconds by typing '!rolloff'" % (self.rolloff_join_interval)
        else:
            text += "Join the rolloff in the next %s seconds by typing '!rolloff'" % (self.rolloff_join_interval)
        client.send_message(text, message.reply(), event=message.event)

        self.rolloff_enable()

        bg_thread = threading.Thread(target=self.background_thread, args=[client, message])
        bg_thread.start()

    def rolloff_enable(self):
        logger.debug("triggered")
        self.rolloff_in_process = True
        self.rolloff_start_time = time.time()
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def rolloff_disable(self):
        logger.debug("triggered")
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def add_user_to_rolloff(self, client, message, user):
        if self.rolloff_in_process:
            elapsed_time = time.time() - self.rolloff_start_time

            if 0 < elapsed_time < self.rolloff_join_interval:
                logger.info("Checking on adding user '%s' to list '%s'" % (user, self.rolloff_rollers_initial))

                if any(x.user_id == user.user_id for x in self.rolloff_rollers_initial):
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
                logger.debug("tied_users are '%s'" % (round_winners_dict['users']))

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
        logger.info('%d initial participants' % (len(initial_participants)))

        self.havocbot.db.add_points_to_user_id(winner_user_object.user_id, len(initial_participants))

        for user in initial_participants:
            if user.user_id != winner_user_object.user_id:
                self.havocbot.db.del_points_to_user_id(user.user_id, 1)

    def background_thread(self, client, message):
        time.sleep(self.rolloff_join_interval)
        logger.debug("triggered")
        self.run_rolloff(client, message, self.rolloff_rollers_initial)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
