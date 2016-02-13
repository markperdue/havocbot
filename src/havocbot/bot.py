import copy
from havocbot import pluginmanager
import inspect
import logging
import sys
import time

logger = logging.getLogger(__name__)


class HavocBot:
    def __init__(self):
        self.clients = []
        self.plugin_dirs = []
        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = []
        self.settings = {}
        self.is_configured = False

    def set_settings(self, **kwargs):
        self.settings['havocbot'] = kwargs.get('havocbot_settings', None)
        self.settings['clients'] = kwargs.get('clients_settings', None)

        self.configure()

    def configure(self):
        self.configure_bot(self.settings['havocbot'])
        self.configure_clients(self.settings['clients'])

        self.load_plugins()

        # The bot is now configured
        self.is_configured = True

    def configure_bot(self, settings_dict):
        """ Configures the bot prior to starting up.

        Takes in a dictionary with keys relating to the bot name with the value
        containg a standard SafeConfigParser.items() tuple list

        example:
        {'havocbot': [('plugins_dir', 'plugins'), ('property2', 'value12)], ...}
        """
        if settings_dict is not None and 'havocbot' in settings_dict:
            for (key, value) in settings_dict['havocbot']:
                if key == 'plugin_dirs':
                    self.plugin_dirs = value.strip().split(",")

    def configure_clients(self, clients_dict):
        """ Configures a client integration prior to starting up.

        Takes in a dictionary with keys relating to the client name with the values
        containg a standard SafeConfigParser.items() tuple list. The client
        names are iterated over and a instance of the client integration is
        instantiated if possible. The tuple list is then passed to the configure()
        method inside the client integration for processing

        example:
        {'slask': [('plugins_dir', 'plugins'), ('property2', 'value12)], ...}
        """

        # Placeholder for client integration instances that will be override the self.clients value
        clientList = []

        if clients_dict is not None:
            # for client_name, client_settings_tuple_list in clients_dict.iteritems():  # Python 3 incompatible
            for client_name, client_settings_tuple_list in clients_dict.items():
                client_temp = self.import_and_return_client(client_name)
                if client_temp is not None:
                    # Instantiates the temp client and passes it the running HavocBot instance
                    client = client_temp(self)

                    if client.configure(client_settings_tuple_list):
                        clientList.append(client)

        # Override the client list with the new temp list
        self.clients = clientList

    # Takes in a name of a module and tries to import it
    def import_and_return_client(self, name, module=None):
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
                        client_instantiator = name

                        if client_instantiator is not None and hasattr(mod, client_instantiator):
                            client = getattr(mod, client_instantiator)
                            return client

        return None

    def import_module(self, name, module=None):
        try:
            if module is None:
                module = "havocbot.clients.%s" % (name)
                __import__(module)
                mod = sys.modules[module]

                return mod
        except ImportError:
            logger.error("Unable to import the %s client integration file" % (name))

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

                # Have the client connect to the client's services
                if client.connect():
                    logger.info("%s client is connected" % (client.integration_name))

                    # Begin client processing
                    client.process()
                else:
                    logger.error("Unable to connect to the client %s" % (client.integration_name))

            # Keep the main thread alive
            while True:
                time.sleep(1)
        else:
            logger.critical("No valid client integrations found. Make sure the settings.ini file has an entry for clients_enabled and that the settings for the client are configured")

    def register_triggers(self, trigger_tuple_list):
        if trigger_tuple_list:
            # Make a shallow copy of the currently known triggers
            working_copy_triggers = copy.copy(self.triggers)
            working_copy_triggers += trigger_tuple_list

            triggers_length = len(trigger_tuple_list)
            triggers_phrase = "trigger" if len(trigger_tuple_list) == 1 else "triggers"
            existing_triggers_length = len(self.triggers)
            existing_triggers_phrase = "trigger" if len(self.triggers) == 1 else "triggers"

            logger.debug("Loading %s new %s. %s %s previously loaded" % (triggers_length, triggers_phrase, existing_triggers_length, existing_triggers_phrase))
            self.triggers = working_copy_triggers

    def unregister_triggers(self, trigger_tuple_list):
        if trigger_tuple_list:
            # Make a shallow copy of the currently known triggers
            working_copy_triggers = copy.copy(self.triggers)
            working_copy_triggers = [x for x in working_copy_triggers not in trigger_tuple_list]

            triggers_length = len(trigger_tuple_list)
            triggers_phrase = "trigger" if len(trigger_tuple_list) == 1 else "triggers"
            existing_triggers_length = len(self.triggers)
            existing_triggers_phrase = "trigger" if len(self.triggers) == 1 else "triggers"

            logger.debug("Removing %s existing %s. %s %s previously loaded" % (triggers_length, triggers_phrase, existing_triggers_length, existing_triggers_phrase))
            self.triggers = working_copy_triggers

    def reload_plugins(self):
        self.plugins_core = pluginmanager.load_plugins_core(self)
        self.plugins_custom = pluginmanager.load_plugins_custom(self)

    def exit(self):
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        self.disconnect()

        self.clients = []
        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = []
        self.is_configured = False

    def disconnect(self):
        for client in self.clients:
            logger.info("Disconnecting client %s" % (client.integration_name))
            client.disconnect()

    def restart(self):
        self.shutdown()
        time.sleep(3)
        self.configure()
        self.start()

    def signal_handler(self, signal, frame):
        logger.info("Received an interrupt. Starting shutdown")
        self.exit()
