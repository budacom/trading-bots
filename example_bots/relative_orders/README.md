# Trading Bots - Relative Orders example

Example use case of Buda.com Bots framework for creating and running cryptocurrency trading bots.

## Overview

Implemented following [DEXBot Relative Orders strategy](https://github.com/Codaone/DEXBot/wiki/The-Relative-Orders-strategy).

This strategy places a buy order below the center price and a sell order above the center price. When both orders fill, the account will have a little more of both assets, as it will have sold for more than it bought. The strategy adds liquidity close to the current price, and so serves traders wanting to buy or sell right now with as little slippage as possible.

Currently this example allows only `Dynamic Center Price`, `Fixed Spread` and `Fixed Order Size`.


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

## Usage

For more references, go to the [official documentation](https://github.com/budacom/trading-bots/blob/master/README.md).

### Setup Config File

Found at `example_bots/relative_orders/configs` folder. Its a yaml file that allows us to easily set parameters.

**Example:**
```yml
market: BTCCLP              # Buda.com market where orders will be placed
prices:
  buy_multiplier: 0.95      # Price multiplier for buy order, ie: 1.05 is 5% above middle price
  sell_multiplier: 1.05     # Price multiplier for sell order, ie: 0.95 is 5% under middle price
amounts:
 max_base: 1                #  Max amount on sell order, ie: base is BTC on BTCCLP
 max_quote: 25000000        #  Max amount on buy order, ie: quote is CLP on BTCCLP

```

## Bot Strategy



### Setup

```python
def _setup(self, config):
    # Set market
    self.market = Market(config['market'])
    # Init variables
    self.bid_price, self.ask_price = None, None
    self.base_amount, self.quote_amount = None, None
    # Set buda trading client
    self.buda = buda.BudaTrading(
        self.market, dry_run=self.dry_run, timeout=self.timeout, logger=self.log, store=self.store)
```

- Initializes placeholders for our `prices` and `amounts`.
- Also setup our buda client and variables according to the `market` on our configs.

### Algorithm

We describe our instructions following our desired automation logic:

```python
def _algorithm(self):
    # Setup
    self.log.info(f'Preparing prices using for {self.market.code}')
    self.prepare_prices()
    # Cancel open orders
    self.log.info('Closing open orders')
    self.cancel_orders()
    # Get available balances
    self.prepare_amounts()
    # Start strategy
    self.log.info('Starting order deployment')
    # Deploy orders
    deploy_list = self.get_deploy_list()
    self.deploy_orders(deploy_list)
```


**Prepare prices**

- First, we get our `market` ticker from buda.com.
- Calculate middle price from `max_bid` and `min_ask` given on our ticker.
- We offset our middle price using our `multipliers` from configs and save them as `bid_price` and `ask_price`.

**Cancel orders**

- Cancel all pending orders at the selected market on Buda.com. This frees balance to use on our orders.

**Prepare Amounts**
- Get amounts from configs to dictate maximum allowed to spend on each order.
- Validates against available balance.
- Sets the amount to be used on orders as quote_amount and base_amount.

**Get Deploy List**
- Builds a list of orders to be deployed.

**Deploy Orders**
- Places our orders at the exchange (You can test with `dry_run=True` flag on global settings to be sure).

### Abort

As important as our strategy is providing abort instructions which is the piece of code that executes in case anything goes wrong:

```python
def _abort(self):
    self.log.error('Aborting strategy, cancelling all orders')
    try:
        self.cancel_orders()
    except Exception:
        self.log.exception(f'Failed!, some orders might not be cancelled')
        raise
    else:
        self.log.info(f'All open orders were cancelled')
```
- Basic abort function, we want to cancel all pending orders and exit.

## Running bots

Test by running the desired bot once from console:
```bash
$ python bots.py run RelativeOrders
```

Flag `--config` can be specified to change the default config file:
```bash
$ python bots.py run RelativeOrders --config /path/to/relative-orders_other.yml
```

Now, we need this to run on a loop, we should use `loop` option indicating `--interval` as seconds:
```bash
$ python bots.py loop RelativeOrders --interval 300
```

Running multiple bots for different markets is possible using multiple shells and config files:

Shell 1:
```bash
$ python bots.py loop RelativeOrders --interval 300 --config relative-orders_btcclp.yml
```
Shell 2:
```bash
$ python bots.py loop RelativeOrders --interval 300 --config relative-orders_ethclp.yml
```


## Contributing

Fork this code, BUIDL bots, submit a pull request :muscle:!
