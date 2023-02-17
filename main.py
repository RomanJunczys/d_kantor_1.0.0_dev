import threading
import time

from bot_dydx import BotdYdX


if __name__ == "__main__":

    bot_dydx = BotdYdX('CRV-USD')
    bot_dydx.cycle_of_bot_life()

    # list_of_bots = []
    #
    # for i in range(0, 3):
    #     list_of_bots.append(BotdYdX('SOL-USD'))
    #
    # list_of_threads = []
    # for bot in list_of_bots:
    #     thread = threading.Thread(target=bot.run_web_socket)
    #     list_of_threads.append(thread)
    #
    # print(f'List of threads: {list_of_threads}')
    #
    # for thread in list_of_threads:
    #     thread.start()
    #     time.sleep(30)
    #     thread.join()
