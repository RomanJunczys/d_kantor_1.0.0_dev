import threading
import time

from bot_dydx import BotdYdX

# security_name
# minimum_order_size  # check for the market minimum order size
# self.rounding_decimal = step_size  # precision
# self.pct_spread = pct_spread  # half of the average hourly candlestick


markets_list = [
    ['SNX-USD', 1.0, 2, 0.7, False],
    ['YFI-USD', 0.001, 0, 0.58, False],
    ['MKR-USD', 0.01, 0, 0.57, False],
    ['CRV-USD', 10.0, 4, 0.52, False],
    ['ICP-USD', 1.0, 2, 0.44, False],
    ['SUSHI-USD', 1.0, 3, 0.43, False],
    ['ENJ-USD', 10.0, 3, 0.42, False],
    ['NEAR-USD', 1.0, 2, 0.41, False],
    ['AVAX-USD', 1.0, 2, 0.4, False],
    ['SOL-USD', 1.0, 3, 0.4, False],
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
