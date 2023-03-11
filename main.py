import threading
import time

from bot_dydx import BotdYdX

# security_name
# minimum_order_size  # check for the market minimum order size
# self.rounding_decimal = step_size  # precision
# self.pct_spread = pct_spread  # half of the average hourly candlestick


markets_list = [
    ['MKR-USD', 0.01, 0, 1.76, False],
    ['SNX-USD', 1.0, 2, 1.44, False],
    ['SOL-USD', 1.0, 3, 1.34, False],
    ['YFI-USD', 0.001, 0, 1.24, False],
    ['MATIC-USD', 10.0, 4, 1.17, False],
]

if __name__ == "__main__":

    bots_list = []
    threads_list = []

    for market in markets_list:
        multiplier = 1

        print(f'Security name {market[0]}'
              f'  minimum order size: {multiplier*market[1]}'
              f'  tick size - precision: {market[2]}'
              f'  pct spread: {market[3]}')

        bot_dydx = BotdYdX(market[0], round(multiplier*market[1], 8), market[2], market[3], market[4])
        bots_list.append(bot_dydx)

    for bot in bots_list:
        thread = threading.Thread(target=bot.cycle_of_bot_life)
        threads_list.append(thread)

    for thread in threads_list:
        thread.start()

    for thread in threads_list:
        thread.join()
