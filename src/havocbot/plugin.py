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
