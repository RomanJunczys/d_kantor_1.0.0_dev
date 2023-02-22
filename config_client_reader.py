import yaml


class ConfigClientReader:
    
    client_config: {}
    
    def __init__(self, account_file_name):
        self.client_file_name = account_file_name
        self.__read_config_account()
    
    def __read_config_account(self):
        with open(self.client_file_name, 'r') as file:
            self.client_config = yaml.safe_load(file)
            return self.client_config
        
    def get_host(self):
        return self.client_config['GENERAL']['HOST']

    #
    def get_default_ethereum_address(self):
        return self.client_config['CLIENT']['DEFAULT_ETHEREUM_ADDRESS']

    #
    def get_stark_private_key(self):
        return self.client_config['CLIENT']['STARK_PRIVATE_KEY']

    def get_stark_public_key(self):
        return self.client_config['CLIENT']['STARK_PUBLIC_KEY']

    #
    def get_api_key(self):
        return self.client_config['CLIENT']['API_KEY']

    def get_api_secret(self):
        return self.client_config['CLIENT']['API_SECRET']

    def get_api_passphrase(self):
        return self.client_config['CLIENT']['API_PASSPHRASE']