import pandas as pd
from dydx3 import Client


class MarketParameters:
    def __init__(self, host, market_name, resolution, limit):
        self.market_name = market_name
        self.resolution = resolution
        self.limit = limit
        self.client = Client(host=host)

    def get_mean_std(self):

        ohlcv = self.get_ohlcv_for_market()

        temp = pd.DataFrame()
        temp['high'] = 100 * (ohlcv.high - ohlcv.low) / ohlcv.low
        mean = temp.high.mean()
        std = temp.high.std()

        # for control only
        print(f'market: {self.market_name}\n'
              f'mean: {mean}\n'
              f'std: {std}')

        return mean, std

    def get_ohlcv_for_market(self):

        candles = self.client.public.get_candles(
            market=self.market_name,
            resolution=self.resolution,
            limit=self.limit)

        # for controls only
        # print(f'Candles data: {candles.data}')

        candles_df = pd.DataFrame(candles.data['candles'])
        columns = ['updatedAt', 'open', 'high', 'low', 'close', 'usdVolume']
        candles_df = candles_df[columns]
        candles_df = candles_df.rename(columns={'updatedAt': 'date', 'usdVolume': 'volume'})
        candles_df['date'] = pd.to_datetime(candles_df['date'])
        candles_df = candles_df.set_index('date')
        candles_df = candles_df.sort_index(ascending=True)
        candles_df = candles_df.astype(float)
        return candles_df
