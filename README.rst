HavocBot
========

.. image:: https://img.shields.io/pypi/v/havocbot.svg
    :target: https://pypi.python.org/pypi/havocbot

HavocBot is an extensible chat bot that works across any number of chat programs




Features
--------

- Connect to multiple chat systems simultaneously
- Plugin system designed to work across all integrated chat clients
- New chat integrations can be dropped into file system for new functionality
- Plugin focus will be on helpful DevOps integrations and work distractions
- More coming soon...




Supported Chat Integrations
---------------

Out of the box, the following chat integrations are supported::

- Slack
- XMPP
- HipChat
- Skype (see note below)

Contributors are encouraged to create their own chat integrations not listed above and to provide them back to the community!


Installation
------------

Install the latest version from pip:

.. code:: bash

    pip install havocbot

Copy the example `main.py`_ and `settings.ini`_ files into a new directory on your machine. Modify the settings.ini to include the neccessary API tokens and server settings for the chat clients that the bot should connect to.

Make sure the chat client is also listed in the 'clients_enabled' field in settings.ini

Open terminal and navigate to the directory where main.py and settings.ini is located

Run the following in terminal:

.. code:: bash

    python main.py

HavocBot should connect to the chat clients if valid credentials were provided




Writing a Plugin
----------------

Coming soon...




Skype Support
-------------

Microsoft has said that support for the Skype API will be dropped at some point in the future so support will be minimal. Skype integration requires some special setup as stated below.

- Skype support is only available in python 2.6 and 2.7 (Skype4Py does not support python 3)
- The Skype desktop application must be running and logged in prior to starting HavocBot and must be ran alongside HavocBot to work.
- If using OSX, 32-bit support through Skype4Py must be forced via:

.. code:: bash

    arch -i386 pip install Skype4Py

- HavocBot must also be forced to run in 32-bit mode on OSX via:

.. code:: bash

    arch -i386 python main.py




Python 2.6 Legacy Compatibility
-------------------------------
- XMPP, HipCHat are compatible out of the box
- Skype support requires an extra pip module to be installed. See `Skype Support` above
- Slack requires an extra pip module to be installed to support python 2.6. SlackClient v0.18.0 depends on 'requests' which requires 'ndg-httpsclient' to enable TLS SNI (See https://github.com/kennethreitz/requests/issues/749#issuecomment-19187417)

.. code:: bash

    pip install ndg-httpsclient




Credits
-------
Mark Perdue (https://github.com/markperdue, https://www.righteousbanana.com)

.. _`main.py`: https://github.com/markperdue/havocbot/tree/master/src/havocbot/examples/main.py
.. _`settings.ini`: https://github.com/markperdue/havocbot/tree/master/src/havocbot/examples/settings.ini
