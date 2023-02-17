

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def print_blue(message):
        print(f'{Colors.OKBLUE}{message}{Colors.ENDC}')

    @staticmethod
    def print_cyan(message):
        print(f'{Colors.OKCYAN}{message}{Colors.ENDC}')

    @staticmethod
    def print_green(message):
        print(f'{Colors.OKGREEN}{message}{Colors.ENDC}')

    @staticmethod
    def print_red(message):
        print(f'{Colors.FAIL}{message}{Colors.ENDC}')

    @staticmethod
    def print_red_bold(message):
        print(f'{Colors.FAIL}{Colors.BOLD}{message}{Colors.ENDC}')

    @staticmethod
    def print_purple(message):
        print(f'{Colors.HEADER}{message}{Colors.ENDC}')
