"""
we will not use real data for this project
we will use mock data instead
"""

import random


class MockData:
    """
    mock data source
    """

    universe = {
        'BTC',
        'ETH',
        'BNB',
        'EOS',
        'USDT',
        'ATOM'
    }  # example trade universe

    def __init__(self):
        pass

    @staticmethod
    def get_price(date, ticker):
        """
        get ticker price for a particular day
        :param date:
        :param ticker:
        :return:
        """
        ticker = ticker.upper()
        if ticker not in MockData.universe:
            raise ValueError(f"{ticker} is not valid. Valid Tickers are {MockData.universe}")

        random_factor = random.random()
        if ticker == "BTC":
            return random_factor * 20000
        if ticker == "ETH":
            return random_factor * 2500
        if ticker == 'BNB':
            return random_factor * 35
        if ticker == 'EOS':
            return random_factor * 4.5
        if ticker == 'ATOM':
            return random_factor * 5.5
        assert ticker == 'USDT'
        return 1