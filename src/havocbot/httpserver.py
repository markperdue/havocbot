
import json
import logging
import threading
from havocbot.message import Message

# Python2/3 compat
try:
    import BaseHTTPServer
except ImportError:
    import http.server as BaseHTTPServer

logger = logging.getLogger(__name__)


class ListenServer(object):
    def __init__(self, havocbot):
        self.havocbot = havocbot
        self.is_enabled = False
        self.server = None
        self.thread = None
        self.port = 8040

    # Takes in a list of kv tuples in the format [('key', 'value'),...]
    def configure(self, settings):
        if settings is not None and settings:
            for item in settings:
                # Switch on the key
                if item[0] == 'http_server_enabled':
                    enabled_value = item[1]
                    if enabled_value.lower() == 'true':
                        self.is_enabled = True
                elif item[0] == 'http_server_port':
                    port_value = int(item[1])
                    if 0 < port_value < 65535:
                        self.port = port_value
                    else:
                        logger.error("http_server_port must be set to a valid port in the settings.ini file")

        return True

    def start(self):
        if self.is_enabled is True:
            self.thread = threading.Thread(target=self.start_listening_server)
            self.thread.start()
        else:
            logger.error("Cannot start the HTTP server. It is not enabled")

    def stop(self):
        logger.info('Stopping HTTP server')
        if self.server is not None:
            self.server.shutdown()

    def start_listening_server(self):
        request_handler = ListenServerHandler
        request_handler.server_version = ''
        request_handler.sys_version = ''
        request_handler.havocbot = self.havocbot  # Set property on handler

        self.server = BaseHTTPServer.HTTPServer(('localhost', self.port), ListenServerHandler)
        logger.info('Starting HTTP server on port %d' % self.port)
        self.server.serve_forever()


class ListenServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    havocbot = None

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_length).decode('utf-8')

        try:
            parsed_json = json.loads(post_body)
        except (TypeError, ValueError) as e:
            logger.info('Invalid json - %s' % e)
            self.send_json_response(400, '{"status": "error", "message": "content not valid json"}')
            return

        parsed_text = parsed_json['text'] if 'text' in parsed_json and len(parsed_json['text']) > 0 else None
        parsed_sender = parsed_json['sender'] if 'sender' in parsed_json and len(parsed_json['sender']) > 0 else None
        parsed_to = parsed_json['to'] if 'to' in parsed_json and len(parsed_json['to']) > 0 else None
        parsed_event = parsed_json['event'] if 'event' in parsed_json and len(parsed_json['event']) > 0 else None
        parsed_client = parsed_json['client'] if 'client' in parsed_json and len(parsed_json['client']) > 0 else None

        if parsed_text and parsed_to and parsed_client and parsed_event:
            message_object = Message(parsed_text, parsed_sender, parsed_to, parsed_event, parsed_client, None)
            if self.havocbot is not None and self.havocbot:
                self.havocbot.process_callback(message_object)

            self.send_json_response(200, '{"status": "ok"}')
        else:
            self.send_json_response(400, '{"status": "error", "message": "missing required fields"}')

    def send_json_response(self, response_code, json_string):
        try:
            self.send_response(response_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json_string.encode("utf-8"))
        except Exception as e:
            logger.error(e)

    def log_message(self, message_format, *args):
        return
