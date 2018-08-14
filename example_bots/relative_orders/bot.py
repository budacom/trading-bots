from collections import namedtuple

from trading_bots.bots import Bot
from trading_bots.contrib.clients import Market, Side
from trading_bots.contrib.clients import buda
from trading_bots.utils import truncate_to


class RelativeOrders(Bot):
    label = 'RelativeOrders'

    def _setup(self, config):
        # Set market
        self.market = Market(config['market'])
        # Init variables
        self.bid_price, self.ask_price = None, None
        self.base_amount, self.quote_amount = None, None
        # Set buda trading client
        self.buda = buda.BudaTrading(
            self.market, dry_run=self.dry_run, timeout=self.timeout, logger=self.log, store=self.store)

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

    def _abort(self):
        self.log.error('Aborting strategy, cancelling all orders')
        try:
            self.cancel_orders()
        except Exception:
            self.log.exception(f'Failed!, some orders might not be cancelled')
            raise
        else:
            self.log.info(f'All open orders were cancelled')

    def prepare_prices(self):
        self.log.info(f'Preparing prices')
        prices_config = self.config['prices']
        ticker = self.buda.get_ticker()
        middle_price = (ticker.max_bid.amount + ticker.min_ask.amount) / 2
        self.log.info(f'{self.market.base} prices:'
                      f' Bid: {ticker.max_bid.amount} | Ask: {ticker.min_ask.amount} | Middle: {middle_price} ')
        # Offset prices from middle using configured price multipliers
        self.bid_price = middle_price * prices_config['buy_multiplier']
        self.ask_price = middle_price * prices_config['sell_multiplier']
        self.log.info(f'{self.market} relative prices: Bid: {self.bid_price} Ask: {self.ask_price}')

    def prepare_amounts(self):
        self.log.info(f'Preparing amounts')
        # Get amounts from configs
        amounts_config = self.config['amounts']
        max_base = amounts_config['max_base']
        max_quote = amounts_config['max_quote']
        # Set final bid and ask amounts
        self.base_amount = min(max_base, self.buda.wallets.base.get_available())
        self.quote_amount = min(max_quote, self.buda.wallets.quote.get_available())
        self.log.debug(' | '.join([
            'Amounts',
            f'Bid: {self.quote_amount} {self.market.quote}',
            f'Ask: {self.base_amount} {self.market.base}'
        ]))

    def get_deploy_list(self):

        Order = namedtuple('order', 'amount price side')
        deploy_list = []

        # Available is on quote currency when side is sell
        def quote_to_base_amount(_amount, _price):
            quote_amount = _amount / _price
            return self.truncate_amount(quote_amount)

        buy_order_price = self.truncate_price(self.bid_price)
        buy_order_amount = quote_to_base_amount(self.quote_amount, buy_order_price)
        sell_order_price = self.truncate_price(self.ask_price)
        sell_order_amount = self.truncate_amount(self.base_amount)

        if buy_order_amount > self.buda.min_order_amount:
            deploy_list.append(Order(buy_order_amount, buy_order_price, Side.BUY))
        if sell_order_amount > self.buda.min_order_amount:
            deploy_list.append(Order(sell_order_amount, sell_order_price, Side.SELL))
        return deploy_list

    def deploy_orders(self, deploy_list: list):
        self.log.info(f'Deploying {len(deploy_list)} new orders')
        for order in deploy_list:
            self.buda.place_limit_order(
                side=order.side,
                amount=order.amount,
                price=order.price,
            )

    def cancel_orders(self, remove_list: list=None):
        remove_list = remove_list or []
        if len(remove_list) > 0:
            self.log.info(f'Canceling {len(remove_list)} orders')
        else:
            self.log.info(f'Canceling open orders')
        self.buda.cancel_orders(remove_list)

    def truncate_amount(self, value):
        return truncate_to(value, self.market.base)

    def truncate_price(self, value):
        return truncate_to(value, self.market.quote)
