from abc import ABCMeta, abstractmethod, abstractproperty


class HavocBotPlugin(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def plugin_description(self):
        """ A brief description of the plugin.

        Read only property that provides an overall description of the plugin.
        This field will be read by the HelpPlugin to provide helpful trigger context

        Args:
            self (HavocBotPlugin): the HavocBotPlugin subclass
        Returns:
            A string that describes the purpose of the plugin
        """
        pass

    @abstractproperty
    def plugin_short_name(self):
        """ A short user friendly name for the plugin.

        Args:
            self (HavocBotPlugin): the HavocBotPlugin subclass
        Returns:
            A string that provides a short user friendly name of the plugin
        """
        pass

    @abstractproperty
    def plugin_usages(self):
        """ Lists usages of the plugin.

        Read only property that defines a grouping of trigger functionality for help
        purposes. This field will be read by the HelpPlugin to provide helpful trigger
        context

        Args:
            self (HavocBotPlugin): the HavocBotPlugin subclass
        Returns:
            A tuple of tuples where the child tuple contains exactly 3 items where:
            1 is a short string that states an available trigger
            2 is a short string that states an example usage of the trigger (can be None)
            3 is a short string that states the purpose of the trigger

            example:
            return (
                ("!help", None, "display basic help information"),
                ("!help plugins", None, "list the enabled plugins"),
                ("!help plugins <plugin>", None, "display detailed information about a specific plugin"),
            )
        """
        pass

    @abstractproperty
    def plugin_triggers(self):
        """ Triggers that will activate the plugin.

        Read only property that defines what the bot will listen for in chats and
        what the bot will call if the event is to be handled.

        Args:
            self (HavocBotPlugin): the HavocBotPlugin subclass
        Returns:
            A string that describes the plugin
        """
        pass

    @abstractmethod
    def init(self, havocbot):
        """ Sets up the basic requirements for a plugin.

        Sets up the triggers dictionary and help dictionary

        Args:
            self (HavocBotPlugin): The HavocBotPlugin subclass
            havocbot (HavocBot): A havocbot instance
        """
        pass

    @abstractmethod
    def configure(self, settings):
        """ Reads a settings bundle and configures the plugin after init has been called.

        The settings bundle comes from reading the settings.ini file and each
        section is converted into a list of tuples

        Args:
            self (HavocBotPlugin): The HavocBotPlugin subclass
            settings (list): a list of key-value tuples

            example:
            [('scramble_duration', 60), ('hint_interval', 14)]
        Returns:
            True/False depending on whether the plugin was able to get configured
        """
        pass

    @abstractmethod
    def shutdown(self):
        """ Performs any work when a shutdown event is triggered.

        This may be called as part of a restart event and should handle any cleanup
        to get the plugin into a restartable state

        Args:
            self (HavocBotPlugin): The HavocBotPlugin subclass
        """
        pass

    @abstractmethod
    def start(self, callback, message, **kwargs):
        """ Must deal with the default entry point for an activated plugin.

        Args:
            self (HavocBotPlugin): The HavocBotPlugin subclass
            callback (Client): A havocbot client instance
            message (Message): A havocbot message subclass instance
            **kwargs: any addional keyword arguments supplied by the client instance
        """
        pass

    def is_valid(self):
        error_string = 'plugin_description must be a non empty string'
        if self.plugin_description is None:
            return (False, error_string)
        if not isinstance(self.plugin_description, str):
            return (False, error_string)
        if len(self.plugin_description) == 0:
            return (False, error_string)

        error_string = 'plugin_short_name must be a non empty string'
        if self.plugin_short_name is None:
            return (False, error_string)
        if not isinstance(self.plugin_short_name, str):
            return (False, error_string)
        if len(self.plugin_short_name) == 0:
            return (False, error_string)

        error_string = 'plugin_usages must be a non empty list containing tuples'
        if self.plugin_usages is None:
            return (False, error_string)
        if not isinstance(self.plugin_usages, list):
            return (False, error_string)
        if len(self.plugin_usages) == 0:
            return (False, error_string)
        if not all(isinstance(elem, tuple) for elem in self.plugin_usages):
            return (False, error_string)

        error_string = 'plugin_triggers must be a non empty list containing tuples'
        if self.plugin_triggers is None:
            return (False, error_string)
        if not isinstance(self.plugin_triggers, list):
            return (False, error_string)
        if len(self.plugin_triggers) == 0:
            return (False, error_string)
        if not all(isinstance(elem, tuple) for elem in self.plugin_triggers):
            return (False, error_string)

        return (True, None)
