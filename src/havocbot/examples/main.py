import errno
import logging
import logging.handlers
import os
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


def create_dir_if_not_exists(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def configure_logging(settings_dict):
    log_file = None
    log_format = None
    log_level = None

    if settings_dict is not None and 'havocbot' in settings_dict:
        for (key, value) in settings_dict['havocbot']:
            if key == 'log_file':
                log_file = value.strip()
            if key == 'log_format':
                log_format = value.strip()
            if key == 'log_level':
                log_level = value.strip()

    if log_file is not None and log_format is not None and log_level is not None:
        log_file_parent_string = os.path.abspath(os.path.join(log_file, os.pardir))
        create_dir_if_not_exists(log_file_parent_string)

        numeric_log_level = getattr(logging, log_level.upper(), None)
        logging.basicConfig(level=numeric_log_level, stream=sys.stdout, format=log_format)
        formatter = logging.Formatter(log_format)
        hdlr = logging.handlers.RotatingFileHandler(log_file, encoding="utf-8", maxBytes=1024 * 1024, backupCount=10)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
    else:
        print("There was a problem configuring the logging system")


def main(settings="settings.ini"):
    parser = SafeConfigParser()
    parser.read(settings)

    settings_dict = {}
    clients_dict = {}

    # Covert the settings.ini settings into a dictionary for later processing
    if parser.has_section('havocbot'):
        # Create a bundle of havocbot settings
        settings_dict['havocbot'] = parser.items('havocbot')

        if parser.has_option('havocbot', 'clients_enabled'):
            clients_string = parser.get('havocbot', 'clients_enabled')
            clients_list = clients_string.strip().split(",")

            # Create a bundle of settings to pass the client integration for processing
            # Bundle format is a list of tuples in the format [('integration name'), [('property1', 'value1'), ('property2', 'value12)], ...]
            for client in clients_list:
                if parser.has_section(client):
                    clients_dict[client] = parser.items(client)
    else:
        sys.exit("Could not find havocbot settings in settings.ini")

    # Configure logging
    configure_logging(settings_dict)

    # Get an instance of the bot if it does not exist
    havocbot = get_bot()

    # Pass a dictionary of settings to the bot
    havocbot.set_settings(havocbot_settings=settings_dict, clients_settings=clients_dict, settings_file=settings)

    # Start it. Off we go
    havocbot.start()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Exiting HavocBot. Come again.")
        if _havocbot.clients is not None and len(_havocbot.clients) > 0:
            _havocbot.shutdown()
        sys.exit(0)
