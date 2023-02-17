from colors import Colors
import websocket
import time
from decimal import Decimal
import json
from dydx3 import Client
import pandas as pd

# constants
from dydx3.constants import ORDER_SIDE_SELL
from dydx3.constants import ORDER_SIDE_BUY
from dydx3.constants import ORDER_TYPE_LIMIT
from dydx3.constants import POSITION_STATUS_OPEN


class BotdYdX:

    def __init__(self, security_name):

        # Connect to the dYdX REST API
        

        self.public_client = Client(host='https://api.dydx.exchange')
        self.security_name = security_name

        self.asks = pd.DataFrame()
        self.bids = pd.DataFrame()

        self.start_time = time.perf_counter()  # for update bot every set time
        self.order_expiration_time = 120
        self.time_between_updates = 110

        account_response = self.private_client.private.get_account()
        self.position_id = account_response.data['account']['positionId']

        self.size = 10  # check for the market
        self.pct_spread = 0.4  # put it in the config file
        self.rounding_decimal = 4  # check for the market

        self.bid_order_id = 0  # buy?
        self.ask_order_id = 0  # sell?
        self.position_balance_id = 0
        self.long_position = True

    def cycle_of_bot_life(self):

        self.start_time = time.perf_counter()  # for update bot every set time

        self.update_order_book()

        while True:

            end_time = time.perf_counter()
            elapsed_time = end_time - self.start_time

            if elapsed_time > self.time_between_updates:

                self.update_order_book()

                self.cancel_buy_order()
                self.create_buy_order()

                self.cancel_sell_order()
                self.create_sell_order()

                self.cancel_position_clear_balance_order()
                self.clear_long_position()
                self.clear_short_position()

                self.start_time = time.perf_counter()

    def update_order_book(self):

        orderbook = self.public_client.public.get_orderbook(
            market=self.security_name)

        print(orderbook.data)

        self.asks = pd.DataFrame(orderbook.data['asks'])
        self.asks = self.asks.astype(float)
        self.asks = self.asks.sort_values(by='price', ascending=True)

        self.bids = pd.DataFrame(orderbook.data['bids'])
        self.bids = self.bids.astype(float)
        self.bids = self.bids.sort_values(by='price', ascending=False)

        Colors.print_red(f'{self.asks.head()}')
        Colors.print_green(f'{self.bids.head()}')

    def cancel_buy_order(self):

        if self.bid_order_id == 0:
            return

        try:
            Colors.print_green(f'Cancel bid (buy) order id: {self.bid_order_id}')
            self.private_client.private.cancel_order(order_id=str(self.bid_order_id))
        except Exception as ex:
            Colors.print_purple(f'Cancel buy order Exception {ex}')
            self.bid_order_id = 0
            Colors.print_green(f'bid order id: {self.bid_order_id}')

        Colors.print_green('Cancel buy order')

    def create_buy_order(self):

        best_bid = self.bids.price.max()

        best_bid_order_price = best_bid - (best_bid * self.pct_spread/100)

        Colors.print_green(f'My best (buy) bid price: {best_bid_order_price:.3f} in order book best bid: {best_bid}')

        order_params = {'position_id': self.position_id, 'market': self.security_name, 'side': ORDER_SIDE_BUY,
                        'order_type': ORDER_TYPE_LIMIT, 'post_only': True, 'size': str(self.size),
                        'price': str(round(best_bid_order_price, self.rounding_decimal)), 'limit_fee': '0.0015',
                        'expiration_epoch_seconds': time.time() + self.order_expiration_time}

        try:
            response_bid_order_dict = self.private_client.private.create_order(**order_params)

            # print(f'(Buy) bid order dict: {response_bid_order_dict.data}')
            bid_order_dict = response_bid_order_dict.data
            self.bid_order_id = bid_order_dict['order']['id']
            Colors.print_green(f'(Buy) bid submitted at {bid_order_dict["order"]["price"]} id: {self.bid_order_id}')

        except Exception as ex:
            Colors.print_purple(f'Create buy (bid) order Exception: {ex}')

        Colors.print_green(f'Create buy (bid) order \n')

    def cancel_sell_order(self):

        if self.ask_order_id == 0:
            return

        try:
            Colors.print_red(f'Cancel ask (sell) order id {self.ask_order_id}')
            self.private_client.private.cancel_order(order_id=str(self.ask_order_id))
        except Exception as ex:
            self.ask_order_id = 0
            Colors.print_red(f'Ask order ID: {self.ask_order_id}')
            Colors.print_purple(f'Cancel ask order exception: {ex}')

        Colors.print_red('Cancel sell order')

    def create_sell_order(self):

        best_ask = self.asks.price.min()

        best_ask_order_price = best_ask + (best_ask * self.pct_spread/100)

        Colors.print_red(f'My ask (sell) price: {best_ask_order_price:.3f} in order book best ask: {best_ask}')

        order_params = {'position_id': self.position_id, 'market': self.security_name, 'side': ORDER_SIDE_SELL,
                        'order_type': ORDER_TYPE_LIMIT, 'post_only': True, 'size': str(self.size),
                        'price': str(round(best_ask_order_price, self.rounding_decimal)), 'limit_fee': '0.0015',
                        'expiration_epoch_seconds': time.time() + self.order_expiration_time}
        try:
            response_ask_order_dict = self.private_client.private.create_order(**order_params)
            # print(f'(Sell) ask order dict: {response_ask_order_dict.data}')
            ask_order_dict = response_ask_order_dict.data
            self.ask_order_id = ask_order_dict['order']['id']
            Colors.print_red(f'(Sell) ask submitted at {ask_order_dict["order"]["price"]} id: {self.ask_order_id}')
        except Exception as ex:
            Colors.print_purple(f'Create sell order Exception: {ex}')

        Colors.print_red('Create sell (ask) order \n')

    def clear_long_position(self):

        all_position = self.private_client.private.get_positions(
            market=self.security_name,
            status=POSITION_STATUS_OPEN,
        )

        if len(all_position.data['positions']) == 0:
            return

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'LONG' and position_size != 0:

            self.long_position = True

            Colors.print_red(f'LONG position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            best_ask = self.asks.price.min()

            Colors.print_red(f'Best ask price in clear long position: {best_ask}')

            position_entry_clear = max(position_price * (1 + self.pct_spread/1000), best_ask)

            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_SELL,
                'order_type': ORDER_TYPE_LIMIT,
                'post_only': True,
                'size': str(position_size),
                'price': str(round(position_entry_clear, self.rounding_decimal)),
                'limit_fee': '0.0015',
                'expiration_epoch_seconds': time.time() + self.order_expiration_time,
            }

            try:
                position_clear_sell_order_response = self.private_client.private.create_order(**order_params)
                self.position_balance_id = position_clear_sell_order_response.data['order']['id']
                Colors.print_red(
                    f"Clearance sell submitted at {position_clear_sell_order_response.data['order']['price']}")
            except Exception as ex:
                Colors.print_purple(f'Clear long position - sell Exception {ex}')

    def clear_short_position(self):

        all_position = self.private_client.private.get_positions(
            market=self.security_name,
            status=POSITION_STATUS_OPEN,
        )

        if len(all_position.data['positions']) == 0:
            return

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'SHORT' and position_size != 0:

            self.long_position = False

            Colors.print_green(f'SHORT position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            best_bid = self.bids.price.max()

            position_entry_clear = min(position_price * (1 - self.pct_spread/1000), best_bid)

            Colors.print_green(f'My best buy (bid) price {position_entry_clear:.1f} '
                               f'best buy (bid) in order book: {best_bid}')

            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_BUY,
                'order_type': ORDER_TYPE_LIMIT,
                'post_only': True,
                'size': str(position_size),
                'price': str(round(position_entry_clear, self.rounding_decimal)),
                'limit_fee': '0.0015',
                'expiration_epoch_seconds': time.time() + self.order_expiration_time,
            }

            try:
                position_clear_sell_order_response = self.private_client.private.create_order(**order_params)
                self.position_balance_id = position_clear_sell_order_response.data['order']['id']
                Colors.print_green(
                    f"Clearance sell submitted at {position_clear_sell_order_response.data['order']['price']}")
            except Exception as ex:
                Colors.print_purple(f'Clear short position - buy - Exception {ex}')

    def cancel_position_clear_balance_order(self):

        if self.position_balance_id == 0:
            return

        try:
            if self.long_position:
                Colors.print_red(f'Cancel position clear balance order: {self.position_balance_id}')
            else:
                Colors.print_green(f'Cancel position clear balance order: {self.position_balance_id}')
            self.private_client.private.cancel_order(order_id=str(self.position_balance_id))
        except Exception as ex:
            self.position_balance_id = 0
            Colors.print_purple(f'Cancel position clear balance order Exception {ex}')

        if self.long_position:
            Colors.print_red(f'Cancel position clear balance order')
        else:
            Colors.print_green(f'Cancel position clear balance order')
