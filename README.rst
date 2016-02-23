HavocBot
========

.. image:: https://img.shields.io/pypi/v/havocbot.svg
    :target: https://pypi.python.org/pypi/havocbot

HavocBot is an extensible chat bot that works across any number of chat programs

Features
--------

- Connect to multiple chat systems simultaneously
- Plugin system designed to work across all integrated chat clients
- New chat client integrations can be dropped into file system for new functionality
- More coming soon...

Installation
------------

Install the latest version from pip

.. code:: bash

    pip install havocbot

Copy the example `main.py`_ and `settings.ini`_ files into a new directory on your machine. Modify the settings.ini to include the neccessary API tokens and server settings for the chat clients that the bot should connect to.

Make sure the chat client is also listed in the 'clients_enabled' field in settings.ini

Open terminal and navigate to the directory where main.py and settings.ini is located.

.. code:: bash

    python main.py

HavocBot should connect to the chat clients if valid credentials were provided


Python 2.6 Legacy Compatibility
-------------------------------
 - XMPP, HipCHat are compatibile out of the box
 - Slack requires an extra pip module to be installed to support python 2.6. SlackClient v0.18.0 depends on 'requests' which requires ndg-httpsclient to support TLS SNI (See https://github.com/kennethreitz/requests/issues/749#issuecomment-19187417)

 .. code:: bash

    pip install ndg-httpsclient




Credits
-------
Mark Perdue (https://github.com/markperdue, https://www.righteousbanana.com)

.. _`main.py`: https://github.com/markperdue/havocbot/tree/master/src/havocbot/examples/main.py
.. _`settings.ini`: https://github.com/markperdue/havocbot/tree/master/src/havocbot/examples/settings.ini
