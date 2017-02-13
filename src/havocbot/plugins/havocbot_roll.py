#!/havocbot

import logging
import random
from random import choice
import threading
import time
from havocbot.exceptions import FormattedMessageNotSentError
from havocbot.message import FormattedMessage
from havocbot.plugin import HavocBotPlugin, Trigger, Usage
from havocbot.user import UserDoesNotExist

logger = logging.getLogger(__name__)


class RollPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'a dice roller'

    @property
    def plugin_short_name(self):
        return 'roll'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!roll', example=None, description='roll a 100 side dice'),
            Usage(command='!highroll', example=None, description='roll a much larger dice'),
            Usage(command='!rolloff', example=None,
                  description='start a rolloff if one is not started or join a rolloff if one is in process'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!roll', function=self.trigger_default, param_dict=None, requires=None),
            Trigger(match='!highroll', function=self.trigger_high_roll, param_dict=None, requires=None),
            Trigger(match='!rolloff', function=self.trigger_rolloff, param_dict=None, requires=None),
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

    def configure(self, settings):
        requirements_met = False

        if settings is not None and settings:
            for item in settings:
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
                    logger.error('There was an issue with the minimal players number. '
                                 'Verify minimum_players is set in the settings file')
            else:
                logger.error('There was an issue with the join interval value. '
                             'Verify join_interval is set in the settings file')

        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def trigger_default(self, client, message, **kwargs):
        roll_result = self._get_roll(100)
        user = None

        try:
            user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        except UserDoesNotExist:
            pass
        finally:
            self.display_roll(client, message, user, roll_result)

    def trigger_high_roll(self, client, message, **kwargs):
        roll_result = self._get_roll(100000000000)
        user = None

        try:
            user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        except UserDoesNotExist:
            pass
        finally:
            self.display_roll(client, message, user, roll_result)

    def _get_roll(self, max_roll):
        return random.SystemRandom().randrange(1, max_roll + 1)

    def display_roll(self, client, message, user_object, roll):
        roll_formatted = '{:,}'.format(roll)  # Format large numbers for Americans

        if user_object is not None:
            text = '%s rolled %s' % (user_object.name, roll_formatted)
        else:
            text = '%s rolled %s' % (message.sender, roll_formatted)

        formatted_message = FormattedMessage(
            text=text,
            fallback_text=text,
            title='Dice Roller',
            thumbnail_url='http://i.imgur.com/eyYARo7.png'
        )

        try:
            client.send_formatted_message(formatted_message, message.reply(), event=message.event, style='icon')
        except FormattedMessageNotSentError as e:
            logger.error("Unable to send formatted message with payload '%s'" % e)
            client.send_message(text, message.reply(), event=message.event)

    def trigger_rolloff(self, client, message, **kwargs):
        try:
            user = self.havocbot.db.find_user_by_username_for_client(message.sender, client.integration_name)
        except UserDoesNotExist:
            text = 'Only known users can do that.'
            client.send_message(text, message.reply(), event=message.event)
        else:
            if not self.rolloff_in_process:
                self._new_rolloff(client, message)

            self._add_user_to_rolloff(client, message, user)

    def _new_rolloff(self, client, message):
        start_phrases = [
            'Time to throw it down.',
            'Let\'s get this started!',
            'Here we go!',
            'Oh doggy!'
        ]
        text = '%s ' % (choice(start_phrases))
        text += 'A %s rolloff has been called. ' % ('regular')

        if self.should_award_points:
            text += "Wager 1 point and join the rolloff in the next %s seconds by typing '!rolloff'" % (
                self.rolloff_join_interval)
        else:
            text += "Join the rolloff in the next %s seconds by typing '!rolloff'" % (self.rolloff_join_interval)

        client.send_message(text, message.reply(), event=message.event)

        self._rolloff_enable()

        bg_thread = threading.Thread(target=self._background_thread, args=[client, message])
        bg_thread.start()

    def _rolloff_enable(self):
        self.rolloff_in_process = True
        self.rolloff_start_time = time.time()
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def _rolloff_disable(self):
        self.rolloff_in_process = False
        self.rolloff_start_time = None
        self.rolloff_rollers_current = []
        self.rolloff_rollers_initial = []

    def _add_user_to_rolloff(self, client, message, user):
        if self.rolloff_in_process:
            elapsed_time = time.time() - self.rolloff_start_time

            if 0 < elapsed_time < self.rolloff_join_interval:
                logger.info("Checking on adding user '%s' to list '%s'" % (user, self.rolloff_rollers_initial))

                if any(x.user_id == user.user_id for x in self.rolloff_rollers_initial):
                    text = 'You are already in this round %s' % (user.name)
                    client.send_message(text, message.reply(), event=message.event)
                else:
                    text = "Added user '%s'" % (user.name)
                    logger.debug(text)
                    self.rolloff_rollers_initial.append(user)
            else:
                text = 'Entries for this round has ended'
                client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'There is no rolloff to join. Aww, nice try'
            client.send_message(text, message.reply(), event=message.event)

    def _run_rolloff_round(self, client, message, round_participants):
        round_winners_dict = {'users': [], 'roll': 0}

        for user_object in round_participants:
            # Sleep to build up some drama
            time.sleep(2)

            roll_result = self._get_roll(100)
            self.display_roll(client, message, user_object, roll_result)

            if roll_result > round_winners_dict['roll']:
                round_winners_dict['users'] = [user_object]
                round_winners_dict['roll'] = roll_result
            elif roll_result == round_winners_dict['roll']:
                round_winners_dict['users'].append(user_object)
                logger.debug("tied_users are '%s'" % (round_winners_dict['users']))

        if len(round_winners_dict['users']) == 1:
            logger.debug('Found a single winner')
            self.rolloff_winner_found = True
        else:
            logger.debug('No single winner found')
            tie_phrases = [
                'A tie?! This cannot be... There can be only one!',
                'What the? A tied score cannot stand. Fixing...',
                'DEALING WITH IT',
                'Everyone is out except for the people tied!'
            ]
            text = '%s' % (choice(tie_phrases))
            client.send_message(text, message.reply(), event=message.event)
            self.rolloff_winner_found = False

        return round_winners_dict

    def _run_rolloff(self, client, message, initial_participants):
        # Create a copy of the original list
        round_participants = list(initial_participants)

        if len(initial_participants) >= self.rolloff_minimum_players:
            winners = None

            self.rolloff_winner_found = False
            while not self.rolloff_winner_found:
                winners = self._run_rolloff_round(client, message, round_participants)

            text = '%s wins with %s' % (winners['users'][0].name, winners['roll'])
            client.send_message(text, message.reply(), event=message.event)

            if self.should_award_points:
                self._award_points(winners['users'][0], initial_participants, client, message)
        else:
            text = 'Not enough players'
            client.send_message(text, message.reply(), event=message.event)

        self._rolloff_disable()

    def _award_points(self, winner_user_object, initial_participants, client, message):
        logger.info('%d initial participants' % (len(initial_participants)))

        try:
            self.havocbot.db.add_points_to_user_id(winner_user_object.user_id, len(initial_participants))
        except UserDoesNotExist:
            logger.error('Unable to add points to user')

        for user in initial_participants:
            if user.user_id != winner_user_object.user_id:
                try:
                    self.havocbot.db.del_points_to_user_id(user.user_id, 1)
                except UserDoesNotExist:
                    logger.error('Unable to remove point from user')

    def _background_thread(self, client, message):
        time.sleep(self.rolloff_join_interval)
        logger.debug('triggered')
        self._run_rolloff(client, message, self.rolloff_rollers_initial)


# Make this plugin available to HavocBot
havocbot_handler = RollPlugin()
