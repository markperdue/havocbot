from havocbot.common import catch_exceptions
from havocbot.plugin import HavocBotPlugin
import imp
import logging
import os

logger = logging.getLogger(__name__)


class StatefulPlugin:
    def __init__(self, havocbot, name, path):
        self.data = None
        self.path = path
        self.name = name
        self.handler = None
        self.init(havocbot)

    # Load a havocbot plugin
    # The handler is set to the exported class instance of the plugin
    @catch_exceptions
    def init(self, havocbot):
        plugin = imp.load_source(self.name, self.path)
        self.handler = plugin.havocbot_handler

        plugin_class_name = self.handler.__class__.__name__
        settings = havocbot.get_settings_for_plugin(plugin_class_name)

        # Call the init method in the plugin
        self.handler.init(havocbot)

        if self.handler.configure(settings):
            logger.debug("%s was configured successfully. Registering plugin triggers..." % (self.name))

            # Register the triggers for the plugin
            havocbot.register_triggers(self.handler.plugin_triggers)
        else:
            logger.error("%s was unable to be configured. Check your settings and try again" % (self.name))

    # Trigger the shutdown of the plugin
    @catch_exceptions
    def shutdown(self):
        self.handler.shutdown()

    @catch_exceptions
    def handle(self, message):
        return self.handler.handle_message(message)

    # Determines if the object at a path is a havocbot plugin
    @staticmethod
    def is_valid(path):
        if not path.endswith(".py"):
            return False

        f = open(path, "rb")
        data = f.read(16)
        f.close()
        if data.startswith(b"#!/havocbot"):
            return True

        return False


# Load a plugin by name
def load_plugin(havocbot, name, path):
    if StatefulPlugin.is_valid(path):
        logger.debug("%s validated as a plugin" % (name))

        return StatefulPlugin(havocbot, name, path)
    else:
        return None


# Load all core plugins and attaches them to the bot
def load_plugins_core(havocbot):
    # Trigger shutdown of any running plugins
    unload_plugins_of_type(havocbot, 'core')

    return load_plugins_of_type(havocbot, 'core')


# Load all custom plugins and attaches them to the bot
def load_plugins_custom(havocbot):
    # Trigger shutdown of any running plugins
    unload_plugins_of_type(havocbot, 'custom')

    return load_plugins_of_type(havocbot, 'custom')


# Load plugins of a type
def load_plugins_of_type(havocbot, plugin_type):
    plugins = []

    if plugin_type == "core":
        # Must load through pkg_resources since the bot may have been setup through pip and full filepaths for resources may not exist
        # http://peak.telecommunity.com/DevCenter/PkgResources#resource-extraction
        import pkg_resources
        core_package = 'havocbot.core'
        resources_list = pkg_resources.resource_listdir(core_package, '')

        for f in resources_list:

            # Remove file extension
            name, ext = os.path.splitext(f)

            if ext == '.py':
                # TODO - Optimize this. resource_filename is slow
                resource_filename = pkg_resources.resource_filename(core_package, f)

                plugin = load_plugin(havocbot, name, resource_filename)
                if plugin and isinstance(plugin.handler, HavocBotPlugin):
                    logger.info("%s core plugin loaded" % (name))
                    plugins.append(plugin)
    elif plugin_type == "custom":
        for listing in havocbot.plugin_dirs:
            folder = os.path.abspath(listing)
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    fpath = os.path.join(folder, f)

                    # Remove file extension
                    body, ext = os.path.splitext(f)

                    plugin = load_plugin(havocbot, body, fpath)
                    if plugin and isinstance(plugin.handler, HavocBotPlugin):
                        logger.info("%s custom plugin loaded" % (body))
                        plugins.append(plugin)
            else:
                logger.error("Plugin directory '%s' was listed in the settings file but does not exist" % (listing))

    return plugins


# Triggers the shutdown method in all loaded plugins
def unload_plugins_of_type(havocbot, plugin_type):
    if plugin_type == "core":
        if havocbot.plugins_core is not None:
            for plugin in havocbot.plugins_core:
                plugin.handler.shutdown()
    elif plugin_type == "custom":
        if havocbot.plugins_custom is not None:
            for plugin in havocbot.plugins_custom:
                plugin.handler.shutdown()
    else:
        return
