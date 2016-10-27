#!/havocbot

import logging
import os.path
import random
import threading
import time
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class ScramblePlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return "scramble some words"

    @property
    def plugin_short_name(self):
        return "scramble"

    @property
    def plugin_usages(self):
        return [
            Usage(command="!scramble", example=None, description="start a round of scramble"),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!scramble', function=self.start_scramble, param_dict=None, requires='scramble:start'),
            Trigger(match="(.*)", function=self.start),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.word_file = None
        self.scramble_duration = None
        self.hint_interval = None
        self.in_process = False
        self.original_word = None
        self.scrambled_word = None
        self.roll_start_time = None

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        requirements_met = False

        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'word_file':
                    self.word_file = item[1]
                elif item[0] == 'scramble_duration':
                    self.scramble_duration = int(item[1])
                elif item[0] == 'hint_interval':
                    self.hint_interval = int(item[1])

        if self.word_file is not None and self.scramble_duration is not None and self.hint_interval is not None:
            if os.path.isfile(self.word_file):
                if self.scramble_duration > 0 and isinstance(self.scramble_duration, int):
                    if self.hint_interval > 0 and isinstance(self.scramble_duration, int):
                        requirements_met = True
                    else:
                        logger.error('There was an issue with the hint interval time. Verify hint_interval is set in the settings file')
                else:
                    logger.error('There was an issue with the scramble duration time. Verify scramble_duration is set in the settings file')
            else:
                logger.error('There was an issue with the word list. Verify word_file is set in the settings file')

        # Return true if this plugin has the information required to connect
        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def start(self, client, message, **kwargs):
        if self.in_process is True:
            if self.does_guess_match_scrambled_word(message.text, self.original_word):
                if message.to:
                    text = "%s got it correct. The answer was '%s'" % (message.sender, self.original_word)
                    client.send_message(text, message.reply(), event=message.event)
                    self.reset_scramble()
        else:
            return

    def start_scramble(self, client, message, **kwargs):
        # Check to see if a scramble has already been started
        if not self.in_process:

            word = self.random_line(self.word_file)
            if word:
                scrambled_word = self.shuffle_word(word)
                if scrambled_word and scrambled_word != 'None':
                    # Get a word, scramble it, and set in_process to True
                    self.in_process = True
                    self.original_word = word
                    self.scrambled_word = scrambled_word
                    logger.info("start_scramble - word is '%s', scrambled_word is '%s'" % (word, scrambled_word))
                    self.roll_start_time = time.time()

                    if message.to:
                        text = "Unscramble the letters to form the word. Guessing is open for %d seconds - '%s'" % (self.scramble_duration, self.scrambled_word)
                        client.send_message(text, message.reply(), event=message.event)

                    verify_original_word = self.original_word

                    helper = RepeatedTimer(self.hint_interval, self.print_letter_of_word, client, message, word)
                    helper.start()
                    bg_thread = threading.Thread(target=self.background_thread, args=[client, message, verify_original_word, helper])
                    bg_thread.start()

                else:
                    text = 'There was an error fetching a scrambled word'
                    client.send_message(text, message.reply(), event=message.event)
            else:
                text = 'There was an error fetching a scrambled word'
                client.send_message(text, message.reply(), event=message.event)
        else:
            text = 'Scramble is already running'
            client.send_message(text, message.reply(), event=message.event)

    def random_line(self, afile):
        return random.choice(open(afile).readlines()).strip()

    def background_thread(self, client, message, verify_original_word, timer):
        time.sleep(self.scramble_duration)
        logger.debug("background_thread - original_word is '%s' and verify_original_word is '%s'" % (self.original_word, verify_original_word))
        if self.in_process and self.original_word == verify_original_word:
            text = "Time's up! The answer was '%s'" % (self.original_word)
            client.send_message(text, message.reply(), event=message.event)
            self.reset_scramble()
            timer.stop()

    def print_letter_of_word(self, timer, client, message, word, index):
        if timer.is_running and self.in_process:
            if (len(word) > index + 1):
                if word == self.original_word:
                    text = "Hint: Character at position %s is '%s'" % (index + 1, word[index])
                    client.send_message(text, message.reply(), event=message.event)
                else:
                    timer.stop()

    def get_hint(self, timer, word, index):
        if timer.is_running and self.in_process:
            if (len(word) > index + 1):
                if word == self.original_word:
                    return (index + 1, word[index])
                else:
                    timer.stop()

        return (None, None)

    def reset_scramble(self):
        self.in_process = False
        self.original_word = None
        self.scrambled_word = None
        self.roll_start_time = None

    def does_guess_match_scrambled_word(self, guess, word):
        if guess == word:
            return True
        else:
            return False

    def shuffle_word(self, word):
        original = word
        word = list(word)
        random.shuffle(word)
        temp_word = ''.join(word)
        logger.debug("shuffle_word - temp_word is '%s'" % (temp_word))
        if temp_word == original or temp_word == 'None':
            logger.debug("shuffle_word - temp_word '%s' is the same as '%s.' Reshuffling" % (temp_word, self.original_word))
            self.shuffle_word(temp_word)
        else:
            logger.debug("shuffle_word - Returning '%s'" % (temp_word))
            return temp_word


class RepeatedTimer(object):
    def __init__(self, interval, function, client, message, word):
        self._timer = None
        self.interval = interval
        self.function = function
        self.client = client
        self.message = message
        self.word = word
        self.is_running = False
        self.index = 0

    def _run(self):
        self.is_running = False
        self.start()
        self.function(self, self.client, self.message, self.word, self.index)
        self.index += 1

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


# Make this plugin available to HavocBot
havocbot_handler = ScramblePlugin()
