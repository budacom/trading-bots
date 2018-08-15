# Trading Bots - Relative Orders example

Example use case of Buda.com Bots framework for creating and running cryptocurrency trading bots.

## Overview

Implemented following [DEXBot Relative Orders strategy](https://github.com/Codaone/DEXBot/wiki/The-Relative-Orders-strategy).

This strategy places a buy order below the center price and a sell order above the center price. When both orders fill, the account will have a little more of both assets, as it will have sold for more than it bought. The strategy adds liquidity close to the current price, and so serves traders wanting to buy or sell right now with as little slippage as possible.

Currently this example allows only `Dynamic Center Price`, `Fixed Spread` and `Fixed Order Size`.

## Installation

Clone or download this repository to your working environment

```bash
git clone https://github.com/budacom/buda-bots.git
```

Install dependencies using pipenv (or pip, of course)

```bash
pipenv install
```

Then, activate the virtual environment:

```bash
pipenv shell
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

Found at `example_bots/relative_orders/configs` folder. Its a `.yaml` file that allows us to easily set parameters.

**Example:**

```yml
market: BTCCLP
prices:
  buy_multiplier: 0.95
  sell_multiplier: 1.05
amounts:
  max_base: 1
  max_quote: 25000000
```

- market: Buda.com market where orders will be placed.
- prices: Price multipliers for buy and sell orders, ie: 1.05 is 5% above middle price.
- amounts: Max amounts on buy and sell orders.

## Bot Strategy

### Setup

```python
def _setup(self, config):
    # Set market
    self.market = Market(config['market'])
    # Set buda trading client
    self.buda = buda.BudaTrading(self.market, self.dry_run, self.timeout, self.log, self.store)
```

- Sets market according to the `market` on our config.
- Setup our Buda.com client for the market.

### Algorithm

We describe our instructions following our desired automation logic:

```python
    def _algorithm(self):
        # PREPARE ORDER PRICES
        # Get middle price
        max_bid, min_ask = self.buda.get_spread_details()
        middle_price = (max_bid + min_ask) / 2
        self.log.info(f'Ticker prices   | Bid: {max_bid} | Ask: {min_ask} | Middle: {middle_price}')
        # Offset prices from middle using configured price multipliers
        prices_config = self.config['prices']
        price_buy = truncate_to(middle_price * prices_config['buy_multiplier'], currency=self.market.quote)
        price_sell = truncate_to(middle_price * prices_config['sell_multiplier'], currency=self.market.quote)
        self.log.info(f'Relative prices | Buy: {price_buy} | Sell: {price_sell}')

        # PREPARE ORDER AMOUNTS
        # Cancel open orders to get correct available amounts
        self.log.info('Closing open orders')
        self.buda.cancel_orders()
        # Fetch available amounts
        available_base = self.buda.wallets.base.get_available()
        available_quote = self.buda.wallets.quote.get_available()
        # Adjust amounts to max in config
        amounts_config = self.config['amounts']
        amount_base = min(amounts_config['max_base'], available_base)
        amount_quote = min(amounts_config['max_quote'], available_quote)
        # Get order buy and sell amounts
        # *quote amount must be converted to base
        amount_buy = truncate_to(amount_quote / price_buy, currency=self.market.base)
        amount_sell = truncate_to(amount_base, currency=self.market.base)
        self.log.info(f'Amounts | Buy {amount_buy} {self.market.quote} | Sell {amount_sell} {self.market.base}')

        # PLACE ORDERS
        self.log.info('Starting order deployment')
        self.buda.place_limit_order(side=Side.BUY, amount=amount_buy, price=price_buy)
        self.buda.place_limit_order(side=Side.SELL, amount=amount_sell, price=price_sell)
```

**Prepare order prices:**

- First, we get the `market spread` from Buda.com's API.
- Calculate middle price from `max_bid` and `min_ask` given on our ticker.
- We offset our middle price using our `multipliers` from configs and save them as `bid_price` and `ask_price`.

**Prepare order amounts:**

- Cancel all pending orders at the selected market on Buda.com. This frees balance to use on our orders.
- Get amounts from configs to dictate maximum allowed to spend on each order.
- Validates against available balance.
- Sets the amount to be used on orders as quote_amount and base_amount.

**Place orders:**

- Builds a list of orders to be deployed.
- Places our orders at the exchange (You can test with `dry_run: True` flag on global settings to be sure).

### Abort

As important as our strategy is providing abort instructions which is the piece of code that executes in case anything goes wrong:

```python
def _abort(self):
    self.log.error('Aborting strategy, cancelling all orders')
    try:
        self.cancel_orders()
    except Exception:
        self.log.critical(f'Failed!, some orders might not be cancelled')
        raise
    else:
        self.log.info(f'All open orders were cancelled')
```

- Basic abort function, we want to cancel all pending orders and exit.

## Running bots

Test by running the desired bot once from console:

```bash
python bots.py run RelativeOrders
```

Flag `--config` can be specified to change the default config file:

```bash
python bots.py run RelativeOrders --config /path/to/your/config.yml
```

Now, we need this to run on a loop, we should use `loop` option indicating `--interval` as seconds:

```bash
python bots.py loop RelativeOrders --interval 300
```

Running multiple bots for different markets is possible using multiple shells and config files:

Shell 1:

```bash
python bots.py loop RelativeOrders --interval 300 --config btcclp.yml
```

Shell 2:

```bash
python bots.py loop RelativeOrders --interval 300 --config ethclp.yml
```

## Contributing

Fork this code, BUIDL bots, submit a pull request :muscle:!
