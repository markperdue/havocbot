#!/havocbot

from havocbot.plugin import HavocBotPlugin
import logging
import random
from random import choice
import threading
import time

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
            ("!roll", None, "roll a 100 side dice "),
            ("!highroll", None, "roll a much larger dice"),
            ("!rolloff", None, "start a rolloff if one is not started or join a rolloff if one is in process"),
        ]

    @property
    def plugin_triggers(self):
        return [
            ("!roll", self.start),
            ("!highroll", self.high_roll),
            ("!rolloff", self.rolloff),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.rolloff_join_window = 5
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = None
        self.rolloff_rollers_initial = None
        self.rolloff_minimum_players = 1

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

    def start(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.sender, channel=message.to)

        if message.to:
            if user is not None:
                text = "%s rolled a %s" % (user.name, random.randrange(1, 101))
            else:
                text = "%s rolled a %s" % (message.sender, random.randrange(1, 101))
            callback.send_message(text, message.to, event=message.event)

    def high_roll(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.sender, channel=message.to)

        if message.to:
            if user is not None:
                text = "%s rolled a %s" % (user.name, random.randrange(1, 10001))
            else:
                text = "%s rolled a %s" % (message.sender, random.randrange(1, 10001))
            callback.send_message(text, message.to, event=message.event)

    def rolloff(self, callback, message, **kwargs):
        user = callback.get_user_by_id(message.sender, channel=message.to)

        if self.rolloff_in_process:
            # Join an existing rolloff if not already in the list
            self.add_user_to_rolloff(callback, message, user)
        else:
            # Start a new rolloff
            self.new_rolloff(callback, message)
            self.add_user_to_rolloff(callback, message, user)

            bg_thread = threading.Thread(target=self.background_thread, args=[callback, message])
            bg_thread.start()

    def new_rolloff(self, callback, message):
        text = "Time to throw it down. A %s rolloff has been called worth dkp. Losers will forfeit 1 point. Join the rolloff in the next %s seconds by typing '!rolloff'" % ('regular', self.rolloff_join_window)
        callback.send_message(text, message.to, event=message.event)

        self.rolloff_enable()

    def rolloff_enable(self):
        self.rolloff_in_process = True
        self.rolloff_start_time = time.time()
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def rolloff_disable(self):
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def add_user_to_rolloff(self, callback, message, user):
        if self.rolloff_in_process:
            elapsed_time = time.time() - self.rolloff_start_time
            if elapsed_time > 0 and elapsed_time < self.rolloff_join_window:
                if user not in self.rolloff_rollers_initial:
                    text = "Added user '%s'" % (user.user_id)
                    logger.debug(text)
                    self.rolloff_rollers_initial.append(user)
                else:
                    text = "%s, you are already in this round" % (user.name)
                    callback.send_message(text, message.to, event=message.event)
            else:
                text = "Entries for this round has ended"
                callback.send_message(text, message.to, event=message.event)
        else:
            text = "There is no rolloff to join. Aww, nice try"
            callback.send_message(text, message.to, event=message.event)

    def roll(self, max_roll):
        return random.SystemRandom().randrange(1, max_roll + 1)

    def run_rolloff_round(self, callback, message, round_participants):
        round_winners_dict = {'users': [], 'roll': 0}

        for user in round_participants:
            # Sleep to build up some drama
            time.sleep(2)

            roll_value = self.roll(5)
            roll_value_formatted = "{:,}".format(roll_value)  # Format large numbers for Americans

            text = "%s rolled %s" % (user.name, roll_value_formatted)
            callback.send_message(text, message.to, event=message.event)

            if roll_value > round_winners_dict['roll']:
                round_winners_dict['users'] = [user]
                round_winners_dict['roll'] = roll_value
            elif roll_value == round_winners_dict['roll']:
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
            callback.send_message(text, message.to, event=message.event)
            self.rolloff_winner_found = False

        return round_winners_dict

    def run_rolloff(self, callback, message, initial_participants):
        # Create a copy of the original list
        round_participants = list(initial_participants)

        if len(initial_participants) >= self.rolloff_minimum_players:
            winners = None

            self.rolloff_winner_found = False
            while not self.rolloff_winner_found:
                logger.debug("Running a rolloff round")
                winners = self.run_rolloff_round(callback, message, round_participants)

            logger.debug("We've got a winner! - %s" % (winners))

            text = "%s wins with a %s" % (winners['users'][0].name, winners['roll'])
            callback.send_message(text, message.to, event=message.event)

            self.rolloff_disable()
        else:
            text = "Not enough players"
            callback.send_message(text, message.to, event=message.event)

        self.rolloff_disable()

    def background_thread(self, callback, message):
        time.sleep(self.rolloff_join_window)
        logger.debug("background_thread - triggered")
        self.run_rolloff(callback, message, self.rolloff_rollers_initial)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
