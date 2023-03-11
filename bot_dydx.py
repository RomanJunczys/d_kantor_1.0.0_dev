import sys
from config_client_reader import ConfigClientReader
from market_parameters import MarketParameters
from colors import Colors
import time
from dydx3 import Client
import pandas as pd

# constants
from dydx3.constants import ORDER_SIDE_SELL
from dydx3.constants import ORDER_SIDE_BUY
from dydx3.constants import ORDER_TYPE_LIMIT
from dydx3.constants import POSITION_STATUS_OPEN
from dydx3.constants import ORDER_TYPE_STOP


class BotdYdX:

    def __init__(self, security_name, minimum_order_size, tick_size, pct_spread, stop_bot):

        self.security_name = security_name
        self.size = minimum_order_size  # check for the market minimum order size
        self.rounding_decimal = tick_size  # check for the market
        self.pct_spread = pct_spread  # half of average hour candle
        self.stop_bot = stop_bot

        # Connect to the dYdX REST API
        config_client_reader = ConfigClientReader('config_client.yaml')

        self.host = config_client_reader.get_host()

        self.private_client = Client(
            host=self.host,
            api_key_credentials={'key': config_client_reader.get_api_key(),
                                 'secret': config_client_reader.get_api_secret(),
                                 'passphrase': config_client_reader.get_api_passphrase()},
            stark_private_key=config_client_reader.get_stark_private_key(),
            default_ethereum_address=config_client_reader.get_default_ethereum_address(),
        )

        self.private_client.private.cancel_all_orders(self.security_name)

        self.public_client = Client(host=config_client_reader.get_host())

        self.asks = pd.DataFrame()
        self.bids = pd.DataFrame()

        self.order_expiration_time = 60 * 60 - 10
        self.time_between_updates = 60 * 60 - 30
        self.time_between_defence = 60 * 10

        account_response = self.private_client.private.get_account()
        self.position_id = account_response.data['account']['positionId']

        self.bid_order_id = 0  # buy?
        self.ask_order_id = 0  # sell?
        self.position_balance_id = 0
        self.long_position = False
        self.short_position = False

    def cycle_of_bot_life(self):

        start_update_time = time.perf_counter()  # for update bot every set time
        start_defence_time = time.perf_counter()  # for defence orders

        self.update_order_book()
        self.update_market_parameters()

        self.clear_long_position()
        self.clear_short_position()

        print(f'Long position {self.long_position}')
        print(f'Short position {self.short_position}')
        print(f'Logic {self.long_position or self.short_position}')

        if not (self.long_position or self.short_position):
            if self.stop_bot:
                self.stop_bot_message()
                return

        self.create_buy_order()
        self.create_sell_order()

        while True:

            # update
            end_update_time = time.perf_counter()
            elapsed_update_time = end_update_time - start_update_time

            if elapsed_update_time > self.time_between_updates:

                self.update_order_book()
                self.update_market_parameters()

                self.cancel_buy_order()
                self.create_buy_order()

                self.cancel_sell_order()
                self.create_sell_order()

                start_update_time = time.perf_counter()

            # defence
            end_defence_time = time.perf_counter()
            elapsed_defence_time = end_defence_time - start_defence_time

            if elapsed_defence_time > self.time_between_defence:

                self.cancel_position_clear_balance_order()
                self.clear_long_position()
                self.clear_short_position()

                print(f'Long position {self.long_position}')
                print(f'Short position {self.short_position}')
                print(f'Logic {self.long_position or self.short_position}')

                start_defence_time = time.perf_counter()

                if not (self.long_position or self.short_position):
                    if self.stop_bot:
                        self.stop_bot_message()
                        return

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

    def update_market_parameters(self):
        resolution = '1HOUR'
        limit = 24
        market_parameters = MarketParameters(self.host, self.security_name, resolution, limit )
        mean, std = market_parameters.get_mean_std()
        self.pct_spread = mean / 2.1

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

        order_params = {'position_id': self.position_id,
                        'market': self.security_name,
                        'side': ORDER_SIDE_BUY,
                        'order_type': ORDER_TYPE_LIMIT,
                        'post_only': True,
                        'size': str(self.size),
                        'price': str(round(best_bid_order_price, self.rounding_decimal)),
                        'limit_fee': '0.0015',
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

        order_params = {'position_id': self.position_id,
                        'market': self.security_name,
                        'side': ORDER_SIDE_SELL,
                        'order_type': ORDER_TYPE_LIMIT,
                        'post_only': True, 'size': str(self.size),
                        'price': str(round(best_ask_order_price, self.rounding_decimal)),
                        'limit_fee': '0.0015',
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
            return False

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'LONG' and position_size != 0:

            self.long_position = True

            Colors.print_red(f'LONG position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            price = round(position_price * (1 + self.pct_spread / 100), self.rounding_decimal)

            Colors.print_red(f'New price: {price:.2f}')

            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_SELL,
                'order_type': ORDER_TYPE_LIMIT,
                'post_only': True,
                'size': str(position_size),
                'price': str(price),
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

        return True

    def clear_long_position_stop(self):

        all_position = self.private_client.private.get_positions(
            market=self.security_name,
            status=POSITION_STATUS_OPEN,
        )

        if len(all_position.data['positions']) == 0:
            return False

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'LONG' and position_size != 0:

            self.long_position = True

            Colors.print_red(f'LONG position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            triggered_price = round(position_price * (1 - 1.0 * self.pct_spread/100), self.rounding_decimal)
            price = round(position_price * (1 - 2.0 * self.pct_spread / 100), self.rounding_decimal)

            Colors.print_red(f'Triggered price: {triggered_price:.2f} '
                               f'price: {price:.2f}')

            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_SELL,
                'order_type': ORDER_TYPE_STOP,
                'post_only': False,
                'size': str(position_size),
                'price': str(price),
                'trigger_price': str(triggered_price),
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

        return True

    def clear_short_position(self):

        all_position = self.private_client.private.get_positions(
            market=self.security_name,
            status=POSITION_STATUS_OPEN,
        )

        if len(all_position.data['positions']) == 0:
            return False

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'SHORT' and position_size != 0:

            self.short_position = True

            Colors.print_green(f'SHORT position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            price = round(position_price * (1 - self.pct_spread / 100), self.rounding_decimal)

            Colors.print_green(f'New price: {price:.2f}')
            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_BUY,
                'order_type': ORDER_TYPE_LIMIT,
                'post_only': True,
                'size': str(position_size),
                'price': str(price),
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

        return True

    def clear_short_position_stop(self):

        all_position = self.private_client.private.get_positions(
            market=self.security_name,
            status=POSITION_STATUS_OPEN,
        )

        if len(all_position.data['positions']) == 0:
            return False

        position_side = all_position.data['positions'][0]['side']
        position_size = abs(float(all_position.data['positions'][0]['size']))

        if position_side == 'SHORT' and position_size != 0:

            self.short_position = True

            Colors.print_green(f'SHORT position {all_position.data}')

            position_price = float(all_position.data['positions'][0]['entryPrice'])

            triggered_price = round(position_price * (1 + 1.0 * self.pct_spread / 100), self.rounding_decimal)
            price = round(position_price * (1 + 2.0 * self.pct_spread / 100), self.rounding_decimal)

            Colors.print_green(f'Triggered price: {triggered_price:.2f} '
                               f'price: {price:.2f}')
            order_params = {
                'position_id': self.position_id,
                'market': self.security_name,
                'side': ORDER_SIDE_BUY,
                'order_type': ORDER_TYPE_STOP,
                'post_only': False,
                'size': str(position_size),
                'price': str(price),
                'trigger_price': str(triggered_price),
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

        return True

    def cancel_position_clear_balance_order(self):

        if self.position_balance_id == 0:
            return

        try:
            if self.long_position:
                Colors.print_red(f'Cancel position clear balance order: {self.position_balance_id}')

            if self.short_position:
                Colors.print_green(f'Cancel position clear balance order: {self.position_balance_id}')

            self.private_client.private.cancel_order(order_id=str(self.position_balance_id))

        except Exception as ex:
            self.position_balance_id = 0
            Colors.print_purple(f'Cancel position clear balance order Exception {ex}')

        if self.long_position:
            Colors.print_red(f'Cancel position clear balance order')

        if self.short_position:
            Colors.print_green(f'Cancel position clear balance order')

    def stop_bot_message(self):
        print(f'\n'
                 f'{Colors.FAIL}{Colors.BOLD}'
                 f'               ##########         \n'
                 f'          ####################    \n'
                 f'     ##############################\n'
                 f'########################################\n'
                 f'   {self.security_name} The bot has been stopped        \n'
                 f'########################################\n'
                 f'     ##############################\n'
                 f'          ####################    \n'
                 f'               ##########         \n'
                 f'{Colors.ENDC}'
                 f'\n')