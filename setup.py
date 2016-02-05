from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()\

setup(
    name='havocbot',
    version='0.1.0.dev3',
    description='an extensible chat bot that works across any number of chat programs',
    long_description=long_description,
    url='https://bitbucket.org/markaperdue/havocbot',
    author='Mark Perdue',
    author_email='markaperdue@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Communications :: Chat',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords=['chat', 'slack', 'jabber', 'xmpp', 'hipchat'],
    packages=find_packages('src', exclude=['havocbot.plugins', 'havocbot.plugins.*']),
    package_dir={'': "src"},
    zip_safe=False,
    install_requires=['requests>=2.6.0', 'sleekxmpp>=1.3.1', 'slackclient>=0.16', 'python-dateutil>=1.4'],
)
