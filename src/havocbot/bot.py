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
        self.triggers = {}
        self.is_configured = False

    def configure(self, **kwargs):
        self.configure_bot(kwargs.get('havocbot_settings', None))
        self.configure_integrations(kwargs.get('integrations_settings', None))

        self.load_plugins()

        # The bot is now configured
        self.is_configured = True

    # Takes in a list of kv tuples in the format [('havocbot'), [('property1', 'value1'), ('property2', 'value12)], ...]
    def configure_bot(self, settings_tuple_list):
        for (bot, settings_tuple) in settings_tuple_list:
            for (key, value) in settings_tuple:
                # Switch on the key
                if key == 'plugin_dirs':
                    self.plugin_dirs = value.strip().split(",")

    # Takes in a list of kv tuples in the format [('integration name'), [('property1', 'value1'), ('property2', 'value12)], ...]
    def configure_integrations(self, integrations_tuple_list):
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
                logger.info("Connecting to %s" % (client.name))

                # Have the client connect to the integration's services
                if client.connect():
                    logger.info("%s client is connected" % (client.name))

                    # Start the integration's processing
                    client.process()
                else:
                    logger.error("Unable to connect to the client %s" % ())
        else:
            logger.critical("No valid chat integrations found. Make sure the settings.ini file has an entry for integrations_enabled and the integration's settings are configured")

    def register_triggers(self, trigger_dict):
        if trigger_dict:
            # logger.debug("Received %s new %s" % (len(trigger_dict), "triggers" if len(trigger_dict) > 1 else "trigger"))
            # for key, value in trigger_dict.items():
            #     logger.debug("Key: '%s', Value: '%s'" % (key, str(value)))

            # Make a shallow copy of the currently known triggers
            updated_triggers = self.triggers.copy()
            updated_triggers.update(trigger_dict)

            # logger.debug("There %s now %d known %s" % ("are" if len(updated_triggers) > 1 else "is", len(updated_triggers), "triggers" if len(updated_triggers) > 1 else "trigger"))
            self.triggers = updated_triggers

    def reload_plugins(self):
        self.plugins_core = pluginmanager.load_plugins_core(self)
        self.plugins_custom = pluginmanager.load_plugins_custom(self)

    def stop(self):
        for client in self.clients:
            logger.debug("disconnecting %s" % (client.name))
            client.disconnect()

        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = {}

    def restart(self):
        self.stop()
        self.load_plugins()
        self.start()
