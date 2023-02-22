import yaml


class ConfigStrategyReader:

    strategy_config: {}
    
    def __init__(self, account_file_name):
        self.account_file_name = account_file_name
        self.__read_strategy_account()
        
    def __read_strategy_account(self):
        with open(self.account_file_name, 'r') as file:
            self.strategy_config = yaml.safe_load(file)
            return self.strategy_config

    # STRATEGY section

    def get_xlm_reserved(self):
        xlm_reserved = float(self.strategy_config['STRATEGY']['XLM_RESERVE'])
        return xlm_reserved

    def get_amount_of_loops(self):
        loops = int(self.strategy_config['STRATEGY']['LOOPS'])
        return loops

    def get_dredger(self):
        dredger = float(self.strategy_config['STRATEGY']['DREDGER'])
        return dredger

    def get_sleep_time(self):
        sleep_time = int(self.strategy_config['STRATEGY']['SLEEP_TIME'])
        return sleep_time

    def get_safe_ask_distance(self):
        safe_ask_distance = float(self.strategy_config['STRATEGY']['SAFE_ASK_DISTANCE'])
        return safe_ask_distance

    def get_safe_bid_distance(self):
        safe_bid_distance = float(self.strategy_config['STRATEGY']['SAFE_BID_DISTANCE'])
        return safe_bid_distance

    def get_max_base_fee(self):
        return self.strategy_config['STRATEGY']['MAX_BASE_FEE']

    def get_push_in(self):
        return float(self.strategy_config['STRATEGY']['PUSH_IN'])

    def get_percent_of_capital(self):
        return float(self.strategy_config['STRATEGY']['PERCENT_OF_CAPITAL'])

    # STATS section

    def get_resolution(self):
        return self.strategy_config['STATS']['RESOLUTION']
    
    def get_limit(self):
        return self.strategy_config['STATS']['LIMIT']

    # PROFIT section

    def get_profit_max_balance(self):
        return float(self.strategy_config['PROFIT']['MAX_BALANCE'])

    def get_profit(self):
        return float(self.strategy_config['PROFIT']['PROFIT'])

    def get_min_portfolio_value(self):
        return float(self.strategy_config['PROFIT']['MIN_PORTFOLIO_VALUE'])
    
    def get_token_to_pay(self):
        return self.strategy_config['PROFIT']['TOKEN_TO_PAY']

    def get_token_to_pay_issuer(self):
        return self.strategy_config['PROFIT']['TOKEN_TO_PAY_ISSUER']
