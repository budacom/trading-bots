[![Buda](https://api.buda.com/images/logo-dark.svg)](https://www.buda.com)

# Trading Bots 🤖

> A simple framework for bootstrapping your **Crypto Trading Bots** on Python 3.6+
> 
> Supported by [Buda.com](https://www.buda.com)
> 
> **Disclaimer:** Still at an early stage of development. Rapidly evolving APIs.

[![PyPI - License](https://img.shields.io/pypi/l/trading-bots.svg)](https://opensource.org/licenses/MIT)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/trading-bots.svg)
[![PyPI](https://img.shields.io/pypi/v/trading-bots.svg)](https://pypi.org/project/trading-bots/)
![PyPI - Status](https://img.shields.io/pypi/status/trading-bots.svg)
[![Updates](https://pyup.io/repos/github/budacom/trading-bots/shield.svg)](https://pyup.io/repos/budacom/delta575/trading-bots/)


**Trading-Bots** is a general purpose *mini-framework* for developing an [algorithmic trading bot](https://en.wikipedia.org/wiki/Algorithmic_trading) on **crypto currencies**, thus it makes no assumption of your trading goals.


## Installation

### Requirements

* macOS, Windows or Linux
* Python 3.6 or 3.7

To install Trading-Bots, simply use `pipenv` (or `pip`, of course):

    $ pipenv install trading-bots

Remember to activate the virtual environment

    $ pipenv shell


## Getting started

Let's learn by example creating a simple bot that fetches your **Bitcoin** balance on [Buda.com](https://www.buda.com)!

We'll assume you have Trading-Bots installed already, and your virtual environment is active.

### Create a project

If this is your first time, you’ll have to take care of some initial setup. Namely, you’ll need to 
auto-generate some code that establishes a Trading-Bots project.

From the command line, cd into a directory where you’d like to store your bots, then run the following command:

    $ bots-admin startproject

    TRADING BOTS 🤖
    ===============

    Name [MyAwesomeProject]: MyProject
    Directory [.]: .

This will create a **my_project** directory in your current directory.

Let’s look at what `startproject` created:

    root/
        bots.py
        secrets.yml
        settings.yml
        my_project/
            __init__.py

These files are:

- The outer `root/` directory is just a container for your project. Its name doesn't matter to Trading-Bots; you can rename it to anything you like.
- `bots.py`: A handy CLI that lets you interact with this Trading-Bots project in various ways.
- `secrets.yml`: A configuration file to store your project secrets like API keys and wallets **DON'T SHARE YOUR SECRETS WITH ANYONE!**
- `settings.yml`: Global settings for this project.
- The inner `my_project/` directory is the actual Python package for your project.
- `my_project/__init__.py`: An empty file that tells Python that this directory should be considered a Python package.

### Create a new bot

Now that your "project" is set up, you're set to start doing work. 

Let's create a simple bot that fetches your **Bitcoin** balance on [Buda.com](https://www.buda.com)!

Each bot you write in Trading-Bots consists of a Python package that follows a certain convention. Trading-Bots comes 
with a utility that automatically generates the basic directory structure of a bot, so you can focus on writing code 
rather than creating directories.

Your bots can live anywhere on your Python path. In this tutorial, we’ll create our bot as a submodule of `my_project`.

To create your bot, make sure you're in the same directory as `bots.py` and type this command:

    $ python bots.py createbot

    TRADING BOTS 🤖
    ===============

    Name [MyAwesomeBot]: MyBot
    Directory (your projects dir): my_project

That’ll create a directory `my_bot`, which is laid out like this:

    my_bot/
        __init__.py
        bot.py
        configs/
            default.yml

This directory structure will house the `MyBot` bot.

You'll also have to *"install"* your new bot, by adding it to the project's `settings.yml` file. 

`settings.yml`
```yaml
installed_bots:
  - my_project.my_bot.bot.MyBot  
```

Configure you Buda.com account's `API_KEY` and `API_SECRET` onto `secrets.yml` credentials:

> You can request your API credentials on you account's profile on [Buda.com](hhtps://www.buda.com)

`secrets.yml`
```yaml
credentials:
  Buda:
    key: MY_API_KEY
    secret: MY_API_SECRET
```

### Write yout first Bot logic

Now let's write the code to fetch the Bitcoin balance on [Buda.com](https://www.buda.com) implementing the Bot's algorithm. The Bot's logic resides in the `my_project/my_bot/bot.py` module created by the `createbot` command:

`my_project/my_bot/bot.py`
```py
# Base class that all Bots must inherit from
from trading_bots.bots import Bot

# The settings module contains all values from settings.yml and secrets.yml
from trading_bots.conf import settings

# API Wrapper for Buda.com
from trading_api_wrappers import Buda


class MyBot(Bot):
    # The label is a unique identifier you assign to your bot on Trading-Bots
    label = 'MyBot'

    def _setup(self, config):
        # Get API_KEY and API_SECRET from credentials
        credentials = settings.credentials['Buda']
        key = credentials['key']
        secret = credentials['secret']

        # Initialize a Buda Auth client
        self.buda = Buda.Auth(key, secret)

    def _algorithm(self):
        # Fetch the Bitcoin balance from Buda.com
        balance = self.buda.balance('BTC')

        # Log the Bitcoin balance
        self.log.info(f'I have {balance.amount.amount} BTC')

    def _abort(self):
        # Abort logic, runs on exception
        self.log.error(f'Something went wrong with MyBot!')
```

### Bot execution

Run the bot!

    $ python bots.py run MyBot

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default

    Starting MyBot 1530691595: 2018-07-04 08:06:35
    I have 1.0 BTC
    Run time: .9972 seconds
    Ending MyBot 1530691595: 2018-07-04 08:06:36

Or put it to work in a loop!

    $ python bots.py loop MyBot --interval 5

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default
    - Interval: 5s

    Starting MyBot 1530692725: 2018-07-04 08:25:25
    I have 1.0 BTC
    Run time: 1.3611 seconds
    Ending MyBot 1530692725: 2018-07-04 08:25:26

    Starting MyBot 1530692735: 2018-07-04 08:25:31
    I have 1.0 BTC
    Run time: 1.3632 seconds
    Ending MyBot 1530692735: 2018-07-04 08:25:32

### Add more features

We can make our Bot a little more modular, let's now fetch our Ethereum balance adding a `currency` key on `MyBot` default config file on `my_project/my_bot/configs/default.yml`:

`my_project/my_bot/configs/default.yml`
```yaml
currency: ETH
```

Now use the new `currency` config on `MyBot` by modifying the Bot's logic:

`my_project/my_bot/bot.py`
```py
from trading_bots.bots import Bot
from trading_bots.conf import settings

from trading_api_wrappers import Buda


class MyBot(Bot):
    label = 'MyBot'

    def _setup(self, config):
        # Get currency from config 
        self.currency = config['currency']

        # Get API_KEY and API_SECRET from credentials
        credentials = settings.credentials['Buda']
        key = credentials['key']        
        secret = credentials['secret']

        # Initialize a Buda Auth client
        self.buda = Buda.Auth(key, secret)

    def _algorithm(self):
        # Fetch the currency balance from Buda.com
        balance = self.buda.balance(self.currency)

        # Log the currency balance
        self.log.info(f'I have {balance.amount.amount} {self.currency}')

    def _abort(self):
        # Abort logic, runs on exception
        self.log.error(f'Something went wrong with MyBot!')
```

Run the bot!

    $ python bots.py run MyBot

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default

    Starting MyBot 1530691595: 2018-07-04 08:06:35
    I have 5.0 ETH
    Run time: .9972 seconds
    Ending MyBot 1530691595: 2018-07-04 08:06:36

Or put it to work in a loop!

    $ python bots.py loop MyBot --interval 10

    TRADING BOTS 🤖
    ===============

    Global settings
    - Settings files: None
    - Logs file: log.txt

    Bot: MyBot
    - Config file: default
    - Interval: 5s

    Starting MyBot 1530692725: 2018-07-04 08:25:25
    I have 5.0 ETH
    Run time: 1.3611 seconds
    Ending MyBot 1530692725: 2018-07-04 08:25:26

    Starting MyBot 1530692735: 2018-07-04 08:25:31
    I have 5.0 ETH
    Run time: 1.3632 seconds
    Ending MyBot 1530692735: 2018-07-04 08:25:32


## Bots CLI

Trading-Bots comes with a handy `CLI` named... `bots-admin`!

### Commands

#### Start a project

    $ python bots.py startproject

```bash
TRADING BOTS 🤖
===============

Name [MyAwesomeProject]: MyProject
Directory [.]: .

Success: 'MyProject' project was successfully created on '.'
```

`startproject` creates a Trading-Bots project directory structure for the given project `NAME` in the current directory `.` or optionally in the given `DIRECTORY`.

    project_dir/
    - project_name/
    - bots.py
    - secrets.yml
    - settings.yml


#### Create a bot

    $ python bots.py createbot

```bash
TRADING BOTS 🤖
===============

Name [MyAwesomeBot]: MyBot
Directory (your projects dir): my_project

Success: 'MyBot' bot was successfully created on 'my_project'
```

`createbot` creates a Bot's directory structure for the given bot `NAME` in the current directory `.` or optionally in the given `DIRECTORY`.

    project_dir/
    - project_name/
    - bots.py
    - secrets.yml
    - settings.yml


After creating or a new Bot, you must add it to `installed_bots` on `settings.yml`:

```yaml
# settings.yml

installed_bots:
  - trading_bots.mybot.bot.MyBot  
```


#### Run bot once

    $ python bots.py run BOT [OPTIONS]

Run a specified `BOT` by label. Options:

|                |     |
| ---            | --- |
| `-c, --config` | Bot configuration filename (YAML format) |
| `-l, --log`    | Log to this file |
| `--settings`   | Global settings files (YAML format) |


```bash
$ python bots.py run Example

TRADING BOTS 🤖
===============

Global settings
- Settings files: None
- Logs file: log.txt

Bot: Example
- Config file: default

Starting Example 1530691595: 2018-07-04 08:06:35
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.9972 seconds
Ending Example 1530691595: 2018-07-04 08:06:40
```

#### Run bot in a loop

    $ python bots.py loop BOT [OPTIONS]

Schedule a `BOT` (by label) to run on an interval. Options:

|                |     |
| ---            | --- |
| `-i, --interval` | Loop interval (in seconds). |
| `-c, --config`   | Bot configuration filename (YAML format) |
| `-l, --log`      | Log to this file |
| `--settings`     | Global settings files (YAML format) |

```bash
$ python bots.py loop Example -i 5

TRADING BOTS 🤖
===============

Global settings
- Settings files: None
- Logs file: log.txt

Bot: Example
- Config file: default
- Interval: 5s

Starting Example 1530692725: 2018-07-04 08:25:25
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.3611 seconds
Ending Example 1530692725: 2018-07-04 08:25:30

Starting Example 1530692735: 2018-07-04 08:25:35
This is an example bot
Doing work for 5 seconds...
Finished!
Run time: 5.3632 seconds
Ending Example 1530692735: 2018-07-04 08:25:40

...
```

### Disclaimer

__USE THE SOFTWARE AT YOUR OWN RISK. YOU ARE RESPONSIBLE FOR YOUR OWN MONEY. PAST PERFORMANCE IS NOT NECESSARILY INDICATIVE OF FUTURE RESULTS.__

__THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.__
