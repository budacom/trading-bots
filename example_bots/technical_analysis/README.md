# Trading Bots - Technical Analysis example

Example use case of Buda.com Bots framework for creating and running cryptocurrency trading bots.

## Overview

Technical analysis uses historical trading data to identify and forecast price trends and patterns which can be exploited with different trading techniques.

Cryptocurrency exchanges share live and publicly all the data needed for this kind of analysis. 
This example shows us how to fetch this data from the markets, build candles from trades using Pandas and easily calculate any indicator using the popular TA-lib.

The algorithm presented as example makes use of Bollinger Bands and Relative Strength Index. We want to identify strong price movements where the market might be oversold or overbought (overreaction or panic selling) making a trade betting for the conditions to return to normal and taking a profit from the price correction.


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

#### **Aditional Dependencies**

##### - Pandas

Pandas is a powerful open source data analysis tool that allows us to easily work with our data arrays. Its available on PyPI:
```bash
$ pipenv install pandas
```

##### - TA-Lib

TA-Lib is an open source library which includes over 200 indicators and pattern recognition for technical analysis of financial market data.

You can follow the install instructions [here](https://github.com/mrjbq7/ta-lib).

Or you might also try these unofficial windows binaries for both 32-bit and 64-bit:

https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

Just download and move the file to your project folder and install, eg: (for python3.7 64bits, change versions accordingly)
```bash
$ mv /path/to/TA_Lib‑0.4.17‑cp37‑cp37m‑win_amd64.whl /path/to/trading-bots
$ pipenv install --skip-lock TA_Lib‑0.4.17‑cp37‑cp37m‑win_amd64.whl
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

Found at `example_bots/simple_limit/configs` folder. Its a yaml file that allows us to easily set parameters.

**Example:**
```yml
market: BTCCLP              # Buda.com market where orders will be placed
reference:
  name: Bitstamp            # Reference exchange to use for price
  market: BTCUSD            # Reference market to use for price
  candle_interval: 5min     # Interval for trades resample to generate candles
talib:
  bbands:
    periods: 14             # Number of periods to calculate Bollinger Bands
  rsi:
    periods: 14             # Number of periods to calculate Relative Strength Index
    overbought: 85          # RSI value to consider the market overbought
    oversold: 15            # RSI value to consider the market oversold
amounts:
 max_base: 1                #  Max amount on sell order, ie: base is BTC on BTCCLP
 max_quote: 500000          #  Max amount on buy order, ie: quote is CLP on BTCCLP
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
    # Set converter
    self.converter = OpenExchangeRates(timeout=self.timeout)
    # Set reference market client
    reference_config = config['reference']
    self.reference = self._get_market_client(reference_config['name'], reference_config['market'])
    assert self.reference.market.base == self.market.base
```

- Initializes placeholders for our `prices` and `amounts`.
- Also setup our clients and variables according to the reference `market` on our configs.

### Algorithm

We describe our instructions following our desired automation logic:

```python
    def _algorithm(self):
        # Update candle data and TA indicators
        self.log.info(f'Getting trades from {self.reference.name} {self.reference.market.code}')
        from_time = time.time() - 60*60*24
        trades = self.get_trades(from_time)
        # Create pandas DataFrame from trades and set date as index
        df = pd.DataFrame(trades)
        df.index = df.timestamp.apply(lambda x: pd.datetime.utcfromtimestamp(x))
        # Build 5min candles from trades DataFrame [open, high, close, low]
        df = df.rate.resample(self.candle_interval).ohlc()
        # Calculate Bolliger Bands and RSI from talib
        df['bb_lower'], df['bb_middle'], df['bb_upper'] = talib.BBANDS(df.close, timeperiod=self.bbands_periods)
        df['rsi'] = talib.RSI(df.close, timeperiod=self.rsi_periods)
        lower = self.truncate_price(df.bb_lower[-1])
        middle = self.truncate_price(df.bb_middle[-1])
        upper = self.truncate_price(df.bb_upper[-1])
        self.log.info(f'BB_lower: {lower} | BB_middle: {middle} | BB_upper: {upper}')
        self.log.info(f'RSI: {df.rsi[-1]:.2f}')
        # Check if our position is open or closed
        if self.position['status'] == 'closed':
            # Try conditions to open position
            self.log.info(f'Position is closed, checking to open')
            if df.close[-1] < df.bb_lower[-1] and df.rsi[-1] < self.rsi_oversold:
                # Last price is lower than the lower BBand and RSI is oversold, BUY!
                self.log.info(f'Market oversold! BUY!')
                amount = self.get_amount(Side.SELL)
                tx = self.buda.place_market_order(Side.SELL, amount)
                self.position = {
                    'status': 'open',
                    'side': Side.SELL.value,
                    'amount': tx.amount.amount
                }
            elif df.close[-1] > df.bb_upper[-1] and df.rsi[-1] > self.rsi_overbought:
                # Last price is higher than the upper BBand and RSI is overbought, SEll!
                self.log.info(f'Market overbought! SEll!')
                amount = self.get_amount(Side.BUY)
                tx = self.buda.place_market_order(Side.BUY, amount)
                self.position = {
                    'status': 'open',
                    'side': Side.BUY.value,
                    'amount': tx.amount.amount
                }
            else:
                self.log.info(f'Market conditions unmet to open position')
        else:
            self.log.info(f'Position is open, checking to close')
            if self.position['side'] == Side.BUY.value and df.rsi[-1] >= 30:
                # RSI is back to normal, close Buy position
                self.log.info(f'Market is back to normal, closing position')
                amount = self.position['amount']
                tx = self.buda.place_market_order(Side.SELL, amount)
                remaining = self.position['amount'] - tx.amount.amount
                if remaining == 0:
                    self.position = {'status': 'closed'}
                else:
                    self.position['amount'] = remaining
            elif self.position['side'] == Side.SELL.value and df.rsi[-1] <= 70:
                # RSI is back to normal, close Sell position
                self.log.info(f'Market is back to normal, closing position')
                amount = self.position['amount']
                tx = self.buda.place_market_order(Side.BUY, amount)
                remaining = self.position['amount'] - tx.amount.amount
                if remaining == 0:
                    self.position = {'status': 'closed'}
                else:
                    self.position['amount'] = remaining
            else:
                self.log.info(f'Market conditions unmet to close position')
        self.store.set('position', self.position)
```


**Building candles from trades**

- Fetch trades from the selected `exchange` and `market`. Save to store.
- Build DataFrame from trades array.
- Resample trades to `candle_interval` set on config.
- Build candles using pandas `ohlc` method.

**TA-Lib indicators**

- Calculate Bollinger Bands and RSI using talib and specified parameters on config.

**Check Market conditions**
- If position is closed, place a buy order if market is oversold according to indicators and RSI parameters on config. Save positon to store.
- If position is closed, place a sell order if market is overbought according to indicators and RSI parameters on config. Save positon to store.
- If position is open, close position if market conditions are back to normal according to position side.


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
$ python bots.py run TechnicalAnalysis
```

Flag `--config` can be specified to change the default config file:
```bash
$ python bots.py run TechnicalAnalysis --config /path/to/technical-analysis_other.yml
```

Now, we need this to run on a loop, we should use `loop` option indicating `--interval` as seconds:
```bash
$ python bots.py loop TechnicalAnalysis --interval 300
```

Running multiple bots for different markets is possible using multiple shells and config files:

Shell 1:
```bash
$ python bots.py loop TechnicalAnalysis --interval 300 --config technical-analysis_btcclp.yml
```
Shell 2:
```bash
$ python bots.py loop TechnicalAnalysis --interval 300 --config technical-analysis_ethclp.yml
```


## Contributing

Fork this code, BUIDL bots, submit a pull request :muscle:!
