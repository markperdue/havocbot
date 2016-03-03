import copy
from havocbot import pluginmanager
import inspect
import logging
import sys
import threading
import time

# Python2/3 compat
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

# Python2/3 compat
try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser

logger = logging.getLogger(__name__)


class HavocBot:
    def __init__(self):
        self.clients = []
        self.queue = Queue()
        self.plugin_dirs = []
        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = []
        self.settings = {}
        self.settings_file = None
        self.is_configured = False
        self.processing_threads = []
        self.should_shutdown = False
        self.should_restart = False

    def set_settings(self, **kwargs):
        self.settings['havocbot'] = kwargs.get('havocbot_settings', None)
        self.settings['clients'] = kwargs.get('clients_settings', None)
        self.settings_file = kwargs.get('settings_file', None)

        self.configure()

    def configure(self):
        self.configure_bot(self.settings['havocbot'])
        self.configure_clients(self.settings['clients'])

        self.load_plugins()

        # The bot is now configured
        logger.debug("HavoceBot instance has been configured")
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

    def get_settings_for_plugin(self, plugin):
        tuple_list = []

        parser = SafeConfigParser()
        parser.read(self.settings_file)

        # Covert the settings.ini settings into a dictionary for later processing
        if parser.has_section(plugin):
            # Create a bundle of plugin settings
            tuple_list = parser.items(plugin)
            logger.debug("Settings found for plugin - '%s'" % (tuple_list))
        else:
            logger.debug("No settings found for plugin '%s'" % (plugin))

        return tuple_list

    def start(self):
        if self.is_configured is not True:
            sys.exit('Havocbot has not been configured. Please configure the bot and try again')
        else:
            logger.info("Starting HavocBot")

        if self.clients is not None and len(self.clients) > 0:
            logger.debug("Setting should_shutdown to False")
            self.should_shutdown = False

            # Connect and begin processing for each client in tuple
            for client in self.clients:
                # Spawn a thread for each unconnected client
                logger.debug("Spawning new daemon thread for client %s" % (client.integration_name))
                t = ClientThread(self)
                t.daemon = True
                self.processing_threads.append(t)
                t.start()

                logger.info("Connecting to %s" % (client.integration_name))

                # Have the client connect to the client's services
                if client.connect():
                    logger.info("%s client is connected" % (client.integration_name))

                    self.queue.put(client)
                else:
                    logger.error("Unable to connect to the client %s" % (client.integration_name))

            # Main thread of the bot
            self.process()
        else:
            logger.critical("No valid client integrations found. Make sure the settings.ini file has an entry for clients_enabled and that the settings for the client are configured")

    def process(self):
        try:
            while threading.activeCount() > 0:
                # logger.debug("Main Loop - active threads: %s, should_shutdown: %s, should_restart: %s" % (threading.activeCount(), self.should_shutdown, self.should_restart))
                # If exit mode is true the bot will be expecting porcessing threads to die off
                # During every loop the bot will be checking to see if background threads have
                # switch to inactive status. If so, the thread will be removed from the active
                # processing thread list
                if self.should_shutdown:
                    #  Updating the list with only the threads that are still active
                    self.processing_threads = [x for x in self.processing_threads if x.is_alive()]

                    # Integrations like xmpp rely on sleekxmpp behind the scenes for processing.
                    # Sleekxmpp spawns its own background threads for scheduling purposes that
                    # take a little while longer to stop then the items in self.processing_threads
                    # so this next conditional will wait not only until HavocBot threads are burned
                    # down but also until the total active threads are down to just the main thread.
                    # This probably should be redone to be cleaner. It is a TODO
                    if len(self.processing_threads) == 0:
                        if threading.activeCount() == 1:
                            logger.debug("Only the main thread is active. All background threads have exited")
                            self.should_shutdown = False
                        else:
                            logger.debug("Waiting on non HavocBot background thread to exit")
                    else:
                        logger.debug("Waiting on HavocBot background thread to exit")
                else:
                    # Reconfigure and restart the bot if coming from a restart event
                    if self.should_restart:
                        self.should_restart = False
                        self.configure()
                        self.start()
                time.sleep(1)
                pass
        except (KeyboardInterrupt, SystemExit) as e:
            logger.info("Interrupt received - %s" % (e))
            # Cleanup before finally exiting
            self.should_shutdown = True
            self.exit()

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

            tmp_list = []
            for x in working_copy_triggers:
                if x not in trigger_tuple_list:
                    tmp_list.append(x)
            working_copy_triggers = tmp_list

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

    def restart(self):
        self.should_restart = True
        self.shutdown()

    def shutdown(self):
        self.disconnect()

        # Need to kill threads
        for thread in self.processing_threads:
            if thread.is_active:
                thread.queue.task_done()
                thread.is_active = False

        self.clients = []
        self.plugins_core = []
        self.plugins_custom = []
        self.triggers = []
        self.is_configured = False

    def disconnect(self):
        self.should_shutdown = True
        for client in self.clients:
            logger.info("Disconnecting client %s" % (client.integration_name))
            client.disconnect()

    def signa_handler(self, signal, frame):
        logger.info("Received an interrupt. Starting shutdown")
        self.exit()

    def show_threads(self):
        for thread in self.processing_threads:
            logger.debug("HavocBot.show_threads() - %s - thread is %s. is_active set to %s, is_alive set to %s" % (len(self.processing_threads), thread, thread.is_active, thread.is_alive()))


class ClientThread(threading.Thread):
    def __init__(self, havocbot):
        threading.Thread.__init__(self)
        self.havocbot = havocbot
        self.queue = havocbot.queue
        self.is_active = True

    def run(self):
        while not self.havocbot.should_shutdown:
            try:
                client = self.queue.get()
                # Trigger the client integration's process() method
                client.process()
            except Exception as e:
                logger.error(e)
            finally:
                if self.is_active:
                    self.queue.task_done()
                    self.is_active = False
