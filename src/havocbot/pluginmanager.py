from havocbot.common import catch_exceptions
from havocbot.plugin import HavocBotPlugin
import imp
import logging
import os

logger = logging.getLogger(__name__)


class StatefulPlugin:
    def __init__(self, havocbot, name, path):
        logger.log(0, "__init__ triggered")

        self.data = None
        self.path = path
        self.name = name
        self.handler = None
        self.init(havocbot)

    # Load a havocbot plugin
    # The handler is set to the exported class instance of the plugin
    @catch_exceptions
    def init(self, havocbot):
        logger.log(0, "init triggered")

        plugin = imp.load_source(self.name, self.path)
        self.handler = plugin.havocbot_handler

        # Call the init method in the plugin
        self.handler.init(havocbot)

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
    logger.log(0, "load_plugin called with name '%s' and path '%s'" % (name, path))

    if StatefulPlugin.is_valid(path):
        logger.debug("%s validated as a plugin" % (name))

        return StatefulPlugin(havocbot, name, path)
    else:
        return None


# Load a plugin by name
def load_plugin_stream(havocbot, name, data_stream):
    logger.log(0, "load_plugin called with name '%s' and data_stream '%s'" % (name, data_stream))

    if StatefulPlugin.is_valid(path):
        logger.debug("%s validated as a plugin" % (name))

        return StatefulPlugin(havocbot, name, path)
    else:
        return None


# Load all core plugins and attaches them to the bot
def load_plugins_core(havocbot):
    logger.log(0, "load_plugins_core triggered")

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
    logger.log(0, "load_plugins_of_type triggered with '%s'" % (plugin_type))

    plugins = []

    if plugin_type == "core":
        # Must load through pkg_resources since the bot may have been setup through pip and full filepaths for resources may not exist
        # http://peak.telecommunity.com/DevCenter/PkgResources#resource-extraction
        import pkg_resources
        core_package = 'havocbot.core'
        resources_list = pkg_resources.resource_listdir(core_package, '')
        # print resources_list
        for f in resources_list:
            # logger.info("<NEW> f is '%s'" % (f))
            # fpath = os.path.join(folder, f)

            # Remove file extension
            name, ext = os.path.splitext(f)
            # logger.info("<NEW> name is '%s', ext is '%s'" % (name, ext))

            if ext == '.py':
                # logger.info("<NEW> name is '%s' and it is a py file" % (name))
                # resource = pkg_resources.resource_string(core_package, f).encode('base64')
                # print resource
                # resource_stream = pkg_resources.resource_string(core_package, f)
                # print resource_stream
                # TODO - Optimize this. resource_filename is slow
                resource_filename = pkg_resources.resource_filename(core_package, f)

            plugin = load_plugin(havocbot, name, resource_filename)
            if plugin and isinstance(plugin.handler, HavocBotPlugin):
                logger.info("%s plugin loaded" % (name))
                plugins.append(plugin)
        # folder = os.path.join(os.path.dirname(__file__), 'core')
        # logger.info("<OLD> folder is '%s'" % (folder))
        # for f in os.listdir(folder):
        #     logger.info("<OLD> f is '%s'" % (f))
        #     fpath = os.path.join(folder, f)
        #     logger.info("<OLD> fpath is '%s'" % (fpath))

        #     # Remove file extension
        #     body, ext = os.path.splitext(f)
        #     logger.info("<OLD> body is '%s', ext is '%s'" % (body, ext))

        #     plugin = load_plugin(havocbot, body, fpath)
        #     if plugin and isinstance(plugin.handler, HavocBotPlugin):
        #         logger.info("%s plugin loaded" % (body))
        #         plugins.append(plugin)
    elif plugin_type == "custom":
        for listing in havocbot.plugin_dirs:
            folder = os.path.abspath(listing)
            for f in os.listdir(folder):
                fpath = os.path.join(folder, f)

                # Remove file extension
                body, ext = os.path.splitext(f)

                plugin = load_plugin(havocbot, body, fpath)
                if plugin and isinstance(plugin.handler, HavocBotPlugin):
                    logger.info("%s plugin loaded" % (body))
                    plugins.append(plugin)

    return plugins


# Triggers the shutdown method in all loaded plugins
def unload_plugins_of_type(havocbot, plugin_type):
    if plugin_type == "core":
        for plugin in havocbot.plugins_core:
            plugin.handler.shutdown()
    elif plugin_type == "custom":
        for plugin in havocbot.plugins_custom:
            plugin.handler.shutdown()
    else:
        return
