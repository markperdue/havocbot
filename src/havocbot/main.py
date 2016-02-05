import logging
import logging.handlers
import sys

# Python2/3 compat
try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser

logger = logging.getLogger()

_havocbot = None


def get_bot():
    global _havocbot
    if not _havocbot:
        from havocbot.bot import HavocBot
        _havocbot = HavocBot()

    return _havocbot


def configure_logging(settings_tuple_list):
    log_file = None
    log_format = None
    log_level = None

    if settings_tuple_list is not None:
        for (bot, settings_tuple) in settings_tuple_list:
            if bot == 'havocbot':
                for (key, value) in settings_tuple:
                    # Switch on the key
                    if key == 'log_file':
                        log_file = value.strip()
                    elif key == 'log_format':
                        log_format = value.strip()
                    elif key == 'log_level':
                        log_level = value.strip()

    if log_file is not None and log_format is not None and log_level is not None:
        logging.basicConfig(level=log_level.upper(), stream=sys.stdout, format=log_format)
        formatter = logging.Formatter(log_format)
        hdlr = logging.handlers.RotatingFileHandler(log_file, encoding="utf-8", maxBytes=1024 * 1024, backupCount=10)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)


def main(settings="settings.ini"):
    try:
        parser = SafeConfigParser()
        parser.read(settings)
    except Exception:
        sys.exit("Could not load settings file: %s" % settings)

    settings_tuple_list = []
    integrations_tuple_list = []

    # Covert the settings.ini settings into a dictionary for later processing
    if parser.has_section('havocbot'):
        # Create a bundle of havocbot settings
        settings_tuple_list = [('havocbot', parser.items('havocbot'))]

        if parser.has_option('havocbot', 'integrations_enabled'):
            integrations_string = parser.get('havocbot', 'integrations_enabled')
            integrations_list = integrations_string.strip().split(",")

            # Create a bundle of settings to pass the client integration for processing
            # Bundle format is a list of tuples in the format [('integration name'), [('property1', 'value1'), ('property2', 'value12)], ...]
            for integration in integrations_list:
                if parser.has_section(integration):
                    integrations_tuple_list.append((integration, parser.items(integration)))
    else:
        sys.exit("Could not find havocbot settings in settings.ini")

    # Configure logging
    configure_logging(settings_tuple_list)

    # Get an instance of the bot if it does not exist
    havocbot = get_bot()

    # Pass a dictionary of settings to the bot
    havocbot.configure(havocbot_settings=settings_tuple_list, integrations_settings=integrations_tuple_list)

    # Start it. Off we go
    havocbot.start()

if __name__ == '__main__':
    main()
