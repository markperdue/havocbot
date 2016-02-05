import logging

logger = logging.getLogger(__name__)


class HavocBotPlugin(object):
    def init(self, havocbot):
        logger.log(0, "init triggered")
        # Do setup work here

    def handle_response(self, message):
        logger.log(0, "handle_response triggered")
        # Handle the message

    def shutdown():
        logger.log(0, "shutdown triggered")
        # Cleanup
