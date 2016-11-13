from abc import ABCMeta, abstractmethod, abstractproperty


class Client(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def integration_name(self):
        """ A name for the client integration.

        Args:
            self (Client): the HavocBotPlugin subclass
        Returns:
            A string that provides the name of the integration
        """
        pass

    @abstractmethod
    def configure(self, settings):
        """ Configures the client prior to startup with a settings bundle.

        The settings bundle comes from reading the settings.ini file and each
        section is converted into a list of tuples

        Args:
            self (Client): the HavocBotPlugin subclass
            settings (list): a list of key-value tuples

            example:
            [('username', 'havocbot'), ('password', 'hunter9')]
        Returns:
            True/False depending on whether the client was configured
        """
        pass

    @abstractmethod
    def connect(self):
        """ Connect to the integration client.

        Args:
            self (Client): the HavocBotPlugin subclass
        Returns:
            True/False depending on whether the client was able to connect
        """
        pass

    @abstractmethod
    def disconnect(self):
        """ Disconnect from the integration client.

        Args:
            self (Client): the HavocBotPlugin subclass
        """
        pass

    @abstractmethod
    def process(self):
        """ Processes incoming and outgoing events while connected to
        the client integration.

        This is the main loop of the chat client that will process all events
        and will generally call the handle_message method to act on an event

        Args:
            self (Client): the HavocBotPlugin subclass
        """
        pass

    @abstractmethod
    def handle_message(self, **kwargs):
        """ Receives an event/message and processes it as needed.

        This is the main processing center of the chat client. It will
        receive nearly all the events direct from the method process()
        and will determine if the event is to be handled by a plugin by
        iterating through the known triggers and checking if there is a
        regex match against the trigger. If a match is found, the function
        for the trigger is called with the following arguments:
        self (Client subclass), message_object (Message subclass), and
        an optional capture_groups kwarg that includes the match.groups()

        Args:
            self (Client): the HavocBotPlugin subclass
            **kwargs: message_object (Message subclass)
        """
        pass

    @abstractmethod
    def send_message(self, text, to, **kwargs):
        """ Sends a single line message.

        Args:
            self (Client): the HavocBotPlugin subclass
            text (str): the message text
            to (str): the message destination
            **kwargs: event (str): the message event (optional)
        Raises:
            AttributeError: Client is likely not connected
            Exception: Unknown error when sending the message
        """
        pass

    @abstractmethod
    def send_messages_from_list(self, text_list, to, **kwargs):
        """ Sends a multi line message.

        Takes in a list of messages and forms them into a multi line message
        dependant on the rules of the client integration. This is often as
        simple as "\n".join(message)

        Args:
            self (Client): the HavocBotPlugin subclass
            text_list (list): the message text list
            to (str): the message destination
            **kwargs: event (str): the message event (optional)
        Raises:
            AttributeError: Client is likely not connected
            Exception: Unknown error when sending the message
        """
        pass

    @abstractmethod
    def get_user_from_message(self, message_sender, **kwargs):
        """ Returns a user object from the sender of a message.

        Args:
            self (Client): the HavocBotPlugin subclass
            message_sender (str): the message channel
            **kwargs: channel (str): the channel (optional),
                      event (str): the message event (optional)
        Returns:
            User object or None
        """
        pass

    @abstractmethod
    def get_users_in_channel(self, channel, **kwargs):
        """ List of users in a chat channel.

        Args:
            self (Client): the HavocBotPlugin subclass
            channel (str): the message channel
            **kwargs: event (str): the message event (optional)
        Returns:
            list that may contain user object
        """
        pass
