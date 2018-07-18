# Trading Bots - Any to Any example

Example use case of Buda.com Bots framework for creating and running cryptocurrency trading bots.

## Overview

Trading Bots allows us to automate any kind of actions allowed by the exchanges APIs. In this example we'll create an automation that makes use of many API actions as well as the internal store of Trading Bots.

Any to Any is an automated payment gateway that allows us to watch for deposits in one currency or even for a specific address. Whenever a deposit is detected (and confirmed), the amount will be converted at market price to the desired currency. Finally an optional automatic withdrawal can be made.

This bot might be useful to vendors as they need the fiat money as soon as the coins are available to avoid volatility, also you can set it to withdraw the funds to your fiat account automatically.

## Installation

Clone or download this repository to your working environment
```bash
$ git clone https://github.com/budacom/buda-bots.git
```

Install dependencies using pipenv (or pip, of course)
```bash
$ pipenv install
```

Then, activate the virtual enviroment:
```bash
$ pipenv shell
```
We are ready!

## Authentication

### API Key

Copy the file `secrets.yml.example` and rename it to `secrets.yml`. Then fill with an API key and secret to access your Buda.com account.

### Warnings

- This library will create live orders at Buda.com cryptocurrency exchange. Please review the code and check all the parameters of your strategy before entering your keys and running the bot.
- This bot makes use of a storage file. Default storage saves data as JSON objects inside store.json file found at the root of this project. This file could contain data essential for the correct execution of this strategy.


## Usage

For more references, go to the [official documentation](https://github.com/budacom/trading-bots/blob/master/README.md).

### Setup Config File

Found at `example_bots/any_to_any/configs` folder. Its a yaml file that allows us to easily set parameters.

**Example:**
```yml
from:
  currency: 'BTC'    # 3 digits currency code
  address: 'Any'     # 'Any' if fiat or every address
to:
  currency: 'CLP'    # 3 digits currency code
  withdraw: True     # True to withdraw converted amount
  address: 'None'    # 'None' if fiat
```

## Bot Strategy



### Setup

```python
def _setup(self, config):
    # Get configs
    self.from_currency = config['from']['currency']
    self.from_address = config['from']['address']
    self.to_currency = config['to']['currency']
    self.to_withdraw = config['to']['withdraw']
    self.to_address = config['to']['address']
    # Set market
    self.market = self._get_market(self.from_currency, self.to_currency)
    # Set side
    self.side = Side.SELL if self.market.base == self.from_currency else Side.BUY
    # Set buda trading client
    self.buda = buda.BudaTrading(
        self.market, dry_run=self.dry_run, timeout=self.timeout, logger=self.log, store=self.store)
    # Get deposits
    self.deposits = self.store.get(self.from_currency + '_deposits') or {}
    # Set start date
    self.start_date = datetime.utcnow()
```

- At setup we initialize our variables and clients according to the `market` built from our configs.

### Algorithm

We describe our instructions following our desired automation logic:

```python
def _algorithm(self):
    # Get new deposits
    self.log.info(f'Checking for new {self.from_currency} deposits')
    self.update_deposits()
    # Convert pending amounts
    self.log.info('Converting pending amounts')
    self.process_conversions()
    # Get available balances
    self.log.info('Processing pending withdrawals')
    self.process_withdrawals()
```


**Update deposits**

- Get new deposits from the indicated `from_currency` on our configs.
- Add new deposits to store file indexed by id.

**Process conversions**
- Checks if any deposit has pending amount to be converted.
- Creates market order for pending conversions.
- Saves converted value on store file.

**Process withdrawals**
- If `withdraw` is enabled on config file, withdraws pending value to desired wallet or fiat account.
- Saves result on store file.

### Abort

As important as our strategy is providing abort instructions which is the piece of code that executes in case anything goes wrong:

```python
def _abort(self):
    pass
```
- Nothing to rollback, just exit.

## Running bots

Test by running the desired bot once from console:
```bash
$ python bots.py run AnyToAny
```

Flag `--config` can be specified to change the default config file:
```bash
$ python bots.py run AnyToAny --config /path/to/any-to-any_other.yml
```

Now, we need this to run on a loop, we should use `loop` option indicating `--interval` as seconds:
```bash
$ python bots.py loop AnyToAny --interval 300
```

Running multiple bots for different markets is possible using multiple shells and config files:

Shell 1:
```bash
$ python bots.py loop AnyToAny --interval 300 --config any-to-any_btc_clp.yml
```
Shell 2:
```bash
$ python bots.py loop AnyToAny --interval 300 --config any-to-any__eth_btc.yml
```


## Contributing

Fork this code, BUIDL bots, submit a pull request :muscle:!
