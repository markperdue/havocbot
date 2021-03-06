#!/havocbot

import logging
from random import shuffle
import requests
from havocbot.plugin import HavocBotPlugin, Trigger, Usage

logger = logging.getLogger(__name__)


class ImagesPlugin(HavocBotPlugin):

    @property
    def plugin_description(self):
        return 'get an image from google images'

    @property
    def plugin_short_name(self):
        return 'images'

    @property
    def plugin_usages(self):
        return [
            Usage(command='!image', example='!image golden gate bridge', description='get an image from google images'),
        ]

    @property
    def plugin_triggers(self):
        return [
            Trigger(match='!image\s*(.*)', function=self.trigger_default, param_dict=None, requires=None),
        ]

    def init(self, havocbot):
        self.havocbot = havocbot
        self.api_key_google = None
        self.api_key_google_cx = None

    def configure(self, settings):
        requirements_met = False

        if settings is not None and settings:
            for item in settings:
                if item[0] == 'api_key_google':
                    self.api_key_google = item[1]
                elif item[0] == 'api_key_google_cx':
                    self.api_key_google_cx = item[1]

        if (self.api_key_google is not None and len(self.api_key_google) > 0) and \
                (self.api_key_google_cx is not None and len(self.api_key_google_cx) > 0):
            requirements_met = True
        else:
            logger.error('There was an issue with the plugin configuration. '
                         'Verify that the 2 following properties are set: api_key_google, api_key_google_cx')

        if requirements_met:
            return True
        else:
            return False

    def shutdown(self):
        self.havocbot = None

    def trigger_default(self, client, message, **kwargs):
        if len(message.text.split()) >= 2:
            capture = kwargs.get('capture_groups', None)
            search_string = '+'.join(capture[0].split())
            if len(search_string) > 1:
                response = self.get_image(search_string)
            else:
                response = 'Provide a better query'
        else:
            response = 'Need to provide a search query'

        if message.to:
            client.send_message(response, message.reply(), event=message.event)

    def get_image(self, search_terms):
        search_terms = search_terms.replace(' ', '+')

        base_api = 'https://www.googleapis.com/customsearch/v1'

        url = '%s?key=%s&cx=%s&q=%s&searchType=image&imgSize=xlarge&alt=json&num=10&start=1' % (
            base_api, self.api_key_google, self.api_key_google_cx, search_terms)
        url2 = '%s?key=%s&cx=%s&q=%s&searchType=image&imgSize=xlarge&alt=json&num=10&start=10' % (
            base_api, self.api_key_google, self.api_key_google_cx, search_terms)

        r = requests.get('%s' % url)
        r2 = requests.get('%s' % url2)

        image_urls = []

        if r is not None:
            if 'items' in r.json():
                for item in r.json()['items']:
                    image_urls.append(item['link'])

        if r2 is not None:
            if 'items' in r2.json():
                for item in r2.json()['items']:
                    image_urls.append(item['link'])

        if image_urls:
            shuffle(image_urls)
            return image_urls[0]
        else:
            return 'Nothing found'


# Make this plugin available to HavocBot
havocbot_handler = ImagesPlugin()
