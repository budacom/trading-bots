from trading_bots.bots import Bot
from trading_bots.contrib.clients import BudaTrading
from trading_bots.contrib.clients import Market, Side
from trading_bots.utils import truncate_to


class RelativeOrders(Bot):
    label = 'RelativeOrders'

    def _setup(self, config):
        # Set market
        self.market = Market(config['market'])
        # Set buda trading client
        self.buda = BudaTrading(self.market, self.dry_run, self.timeout, self.log, self.store)

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

    def _abort(self):
        self.log.error('Aborting strategy, cancelling all orders')
        try:
            self.buda.cancel_orders()
        except Exception:
            self.log.critical(f'Failed!, some orders might not be cancelled')
            raise
        else:
            self.log.info(f'All open orders were cancelled')
