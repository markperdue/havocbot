from havocbot.common import catch_exceptions
from havocbot.plugin import HavocBotPlugin
import imp
import logging
import os

logger = logging.getLogger(__name__)


class StatefulPlugin:
    def __init__(self, havocbot, name, path):
        self.path = path
        self.name = name
        self.handler = None
        self.is_validated = False
        self.init(havocbot)

    # Load a havocbot plugin
    # The handler is set to the exported class instance of the plugin
    @catch_exceptions
    def init(self, havocbot):
        # Get the settings bundle for the plugin
        plugin_settings = havocbot.get_settings_for_plugin(self.name)

        # Look for any dependencies listed in the settings bundle
        dependencies_string = next((obj[1] for obj in plugin_settings if obj[0] == 'dependencies'), None)
        if dependencies_string is not None:
            # Do dependency work
            if did_process_dependencies_for_plugin(self.name, dependencies_string, havocbot) is True:
                self.load_plugin(plugin_settings, havocbot)
        else:
            self.load_plugin(plugin_settings, havocbot)

    def load_plugin(self, plugin_settings, havocbot):
        try:
            plugin = imp.load_source(self.name, self.path)
            self.handler = plugin.havocbot_handler

            # Check if plugin is valid. Returns a tuple of format (True/False, None/'error message string')
            result_tuple = self.handler.is_valid()
            if result_tuple[0] is True:
                logger.debug("%s plugin passed validation" % (self.name))

                # Call the init method in the plugin
                self.handler.init(havocbot)

                if self.handler.configure(plugin_settings):
                    logger.debug("%s was configured successfully. Registering plugin triggers" % (self.name))

                    # Register the triggers for the plugin
                    havocbot.register_triggers(self.handler.plugin_triggers)

                    # Confirm that the plugin has now been validated
                    self.is_validated = True
                else:
                    logger.error("%s was unable to be configured. Check your settings and try again" % (self.name))
            else:
                logger.error("%s plugin failed validation and was not loaded - %s" % (self.name, result_tuple[1]))
        except ImportError as e:
            logger.error("%s plugin failed to import. Install any missing third party dependencies and try again - %s" % (self.name, e))

    # Determines if the object at a path is a havocbot plugin
    @staticmethod
    def is_havocbot_file(path):
        if not path.endswith(".py"):
            return False

        f = open(path, "rb")
        data = f.read(16)
        f.close()
        if data.startswith(b"#!/havocbot"):
            return True

        return False


def did_process_dependencies_for_plugin(plugin_name, dependencies_string, havocbot):
    result = False

    if dependencies_string is not None:
        dependency_tuple_list = [(x[0], x[1]) for x in (x.split(':') for x in dependencies_string.split(','))]

        if dependency_tuple_list is not None and len(dependency_tuple_list) > 0:
            dependencies_formatted = ', '.join("%s (%s)" % (t[0], t[1]) for t in dependency_tuple_list)
            logger.info("%s plugin requires third party dependencies prior to startup - %s" % (plugin_name, dependencies_formatted))

            # Get setting from havocbot
            plugins_can_install_modules = havocbot.get_havocbot_setting_by_name('plugins_can_install_modules')

            if plugins_can_install_modules.lower() == 'true':
                logger.info("global setting 'plugins_can_install_modules' is set to True. Installing plugin dependencies")
                result = install_dependencies(plugin_name, dependency_tuple_list, havocbot)
            else:
                result = True

    return result


def install_dependencies(plugin_name, dependency_tuple_list, havocbot):
    if dependency_tuple_list is not None and len(dependency_tuple_list) > 0:
        import pip

        arg_list = ['install']
        for (pip_module_name, pip_module_version) in dependency_tuple_list:
            arg_list.append("%s%s" % (pip_module_name, pip_module_version))

        try:
            return_code = pip.main(arg_list)

            # Fix for pip leaking root handlers. See https://github.com/pypa/pip/issues/3043
            havocbot.reset_logging()

            logger.info("install_dependencies - return_code is '%s'" % (return_code))
            if return_code == 0:
                logger.debug("%s plugin dependencies installed successfully or requirements already satisfied" % (plugin_name))
                return True
            else:
                # logger.error(output.splitlines()[-1].decode('ascii'))  # decode for python3 compatibility
                logger.error("%s plugin dependencies were unable to be installed" % (plugin_name))
        # Catch pip not being installed
        except OSError as e:
            logger.error("Is pip installed? Unable to install plugin dependencies - %s" % (e))
            return False

        return False


# Load a plugin by name
def load_plugin(havocbot, name, path):
    if StatefulPlugin.is_havocbot_file(path):
        logger.debug("%s is a havocbot file and passed first round of validation" % (name))

        return StatefulPlugin(havocbot, name, path)

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
                if plugin and isinstance(plugin.handler, HavocBotPlugin) and plugin.is_validated is True:
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
                    if plugin and isinstance(plugin.handler, HavocBotPlugin) and plugin.is_validated is True:
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
                # Unregister the triggers set for the plugin
                havocbot.unregister_triggers(plugin.handler.plugin_triggers)

                plugin.handler.shutdown()
    elif plugin_type == "custom":
        if havocbot.plugins_custom is not None:
            for plugin in havocbot.plugins_custom:
                # Unregister the triggers set for the plugin
                havocbot.unregister_triggers(plugin.handler.plugin_triggers)

                plugin.handler.shutdown()
    else:
        return
