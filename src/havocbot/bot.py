from havocbot import pluginmanager
import inspect
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HavocBot:
    def __init__(self):
        self.clients = ()
        self.plugin_dirs = []
        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = ()
        self.is_configured = False

    def configure(self, **kwargs):
        self.configure_bot(kwargs.get('havocbot_settings', None))
        self.configure_integrations(kwargs.get('integrations_settings', None))

        self.load_plugins()

        # The bot is now configured
        self.is_configured = True

    def configure_bot(self, settings_tuple_list):
        """ Configures the bot prior to starting up.

        Takes in a list containing a tuple and another list containing key-value
        pair tuples.

        example:
        [('havocbot'), [('plugins_dir', 'plugins'), ('property2', 'value12)], ...]
        """
        for (bot, settings_tuple) in settings_tuple_list:
            for (key, value) in settings_tuple:
                # Switch on the key
                if key == 'plugin_dirs':
                    self.plugin_dirs = value.strip().split(",")

    def configure_integrations(self, integrations_tuple_list):
        """ Configures a client integration prior to starting up.

        Takes in a list containing a tuple containing a client integratation
        name and another list containing key-value pair tuples. The integration
        names are iterated over and a instance of the integration is
        instantiated if possible. The tuple bundle is then passed to the configure()
        method inside the client integration for processing

        example:
        [('slask'), [('plugins_dir', 'plugins'), ('property2', 'value12)], ...]
        """

        # Placeholder for integration instances that will be coverted to a tuple of integration instances
        clientList = []

        for (integration_name, integrations_tuple) in integrations_tuple_list:
            plugin = self.import_and_return_integration(integration_name)
            if plugin is not None:
                new_integration = plugin(self)

                if new_integration.configure(integrations_tuple):
                    clientList.append(new_integration)

        # Convert the list into a tuple for immutability
        self.clients = tuple(clientList)

    # Takes in a name of a module and tries to import it
    def import_and_return_integration(self, name, module=None):
        mod = self.import_module(name, module=None)

        # Inspect the module and iterate over all the members looking for entries that are classes that inherit from client.Client
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj):
                base_classes = inspect.getmro(obj)
                # Get the parent which should always appear as the second item
                parent = base_classes[1]
                if parent is not None:
                    if parent.__name__ == 'Client':
                        # logger.debug("Name: %s, Object: %s, Base Classes: %s" % (name, obj, base_classes))
                        integration_instantiator = name

                        if integration_instantiator is not None and hasattr(mod, integration_instantiator):
                            integration = getattr(mod, integration_instantiator)
                            return integration

        return None

    def import_module(self, name, module=None):
        try:
            if module is None:
                module = "havocbot.integrations.%s" % (name)
                __import__(module)
                mod = sys.modules[module]

                return mod
        except ImportError:
            logger.error("Unable to import the %s integration file" % (name))

            return None

    def load_plugins(self):
        self.plugins_core = pluginmanager.load_plugins_core(self)
        self.plugins_custom = pluginmanager.load_plugins_custom(self)

    def start(self):
        if self.is_configured is not True:
            sys.exit('Havocbot has not been configured. Please configure the bot and try again')
        else:
            logger.info("Starting HavocBot")

        if self.clients is not None and len(self.clients) > 0:
            # Connect and begin processing for each client in tuple
            for client in self.clients:
                logger.info("Connecting to %s" % (client.integration_name))

                # Have the client connect to the integration's services
                if client.connect():
                    logger.info("%s client is connected" % (client.integration_name))

                    # Start the integration's processing
                    client.process()
                else:
                    logger.error("Unable to connect to the client %s" % (client.integration_name))
        else:
            logger.critical("No valid chat integrations found. Make sure the settings.ini file has an entry for integrations_enabled and the integration's settings are configured")

    def register_triggers(self, trigger_tuples):
        if trigger_tuples:
            # Make a shallow copy of the currently known triggers
            working_copy_triggers = self.triggers
            working_copy_triggers += trigger_tuples

            # logger.debug("There %s now %d known %s" % ("are" if len(working_copy_triggers) > 1 else "is", len(working_copy_triggers), "triggers" if len(working_copy_triggers) > 1 else "trigger"))
            self.triggers = working_copy_triggers

    def unregister_triggers(self, trigger_tuples):
        if trigger_tuples:
            # Make a shallow copy of the currently known triggers
            # TODO fix this
            working_copy_triggers = self.triggers
            working_copy_triggers -= trigger_tuples

            # logger.debug("There %s now %d known %s" % ("are" if len(working_copy_triggers) > 1 else "is", len(working_copy_triggers), "triggers" if len(working_copy_triggers) > 1 else "trigger"))
            self.triggers = working_copy_triggers

    def reload_plugins(self):
        self.plugins_core = pluginmanager.load_plugins_core(self)
        self.plugins_custom = pluginmanager.load_plugins_custom(self)

    def stop(self):
        for client in self.clients:
            logger.debug("disconnecting %s" % (client.integration_name))
            client.disconnect()

        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = ()

    def restart(self):
        self.stop()
        self.load_plugins()
        self.start()
