import logging

logger = logging.getLogger(__name__)


class Client(object):
    # All subclassed client integration classes must call this init method and provide it an instance of havocbot
    def __init__(self, havocbot):
        logger.log(0, "__init__ triggered")

        self.name = None
        self.token = None
        self.username = None
        self.password = None
        # Do any __init__() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        logger.log(0, "configure triggered")
        # Do any configure() work here

    # Optional hook from the integration subclass to do any super() work
    # This method should return a boolean of either True or False depending on whether the connect() succeeds
    def connect(self):
        logger.log(0, "connect triggered")
        # Do any connect() work here
        return False

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def disconnect(self):
        logger.log(0, "disconnect triggered")
        # Do any shutdown() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def shutdown(self):
        logger.log(0, "shutdown triggered")
        # Do any shutdown() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def process(self):
        logger.log(0, "process triggered")
        # Do any process() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def handle_message(self, **kwargs):
        logger.log(0, "handle_message triggered")
        # Do any handle_message() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def send_message(self, **kwargs):
        logger.log(0, "send_message triggered")
        # Do any send_message() work here

    # Optional hook from the integration subclass to do any super() work
    # Generally, nothing should be done here
    def send_messages_from_list(self, **kwargs):
        logger.log(0, "send_messages_from_list triggered")
        # Do any send_message() work here
