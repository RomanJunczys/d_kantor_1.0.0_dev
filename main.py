import threading
import time

from bot_dydx import BotdYdX

# security_name
# minimum_order_size  # check for the market minimum order size
# self.rounding_decimal = tick_size  # precision
# self.pct_spread = pct_spread  # half of the average hourly candlestick


markets_list = [
    ['FIL-USD', 1.0, 2, 1.54],
    ['ICP-USD', 1.0, 2, 0.97],
    ['COMP-USD', 0.1, 1, 0.97],
    ['SOL-USD', 1.0, 3, 0.92],
    ['1INCH-USD', 10, 3, 1.9],
]

if __name__ == "__main__":

    bots_list = []
    threads_list = []

    for market in markets_list:
        multiplier = 3

        print(f'Security name {market[0]}'
              f'  minimum order size: {multiplier*market[1]}'
              f'  tick size - precision: {market[2]}'
              f'  pct spread: {market[3]}')

        bot_dydx = BotdYdX(market[0], round(multiplier*market[1], 8), market[2], market[3])
        bots_list.append(bot_dydx)

    for bot in bots_list:
        thread = threading.Thread(target=bot.cycle_of_bot_life)
        threads_list.append(thread)

    for thread in threads_list:
        thread.start()

    for thread in threads_list:
        thread.join()
