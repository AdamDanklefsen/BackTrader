import backtrader as bt

import numpy as np
import pandas as pd
import yfinance as yf

from btplotting import BacktraderPlotting
from btplotting.schemes import Tradimo


class PCFWrapper():
    def log(self, txt, dt=None):
        if self.verbose:
            if dt is not None:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(f'{txt}')

    def __init__(self, start_Date, end_date, TickerA, TickerB, verbose=False, d=0.6):
        self.start_Date = start_Date
        self.end_date = end_date
        self.TickerA = TickerA
        self.TickerB = TickerB
        self.verbose = verbose
        self.d = d

        self.A = yf.download(self.TickerA, self.start_Date, self.end_date).xs(self.TickerA, level='Ticker', axis=1, drop_level=True)
        self.B = yf.download(self.TickerB, self.start_Date, self.end_date).xs(self.TickerB, level='Ticker', axis=1, drop_level=True)
        self.log(f"Downloaded data for {self.TickerA}  from {self.A.index[0]} to {self.A.index[-1]}")
        self.log(f"Downloaded data for {self.TickerB}  from {self.B.index[0]} to {self.B.index[-1]}")
        self.dataA = bt.feeds.PandasData(dataname=self.A, name=self.TickerA)
        self.dataB = bt.feeds.PandasData(dataname=self.B, name=self.TickerB)

        self.cerebro = bt.Cerebro()
        self.cerebro.adddata(self.dataA)
        self.cerebro.adddata(self.dataB)

        from Strategies.Pairs_Copula_Frac import PCFracStrategy
        self.cerebro.addstrategy(
            PCFracStrategy,
            d=self.d,
            verbose=self.verbose
        )

        self.cerebro.broker.setcash(100000.0)
        self.cerebro.broker.setcommission(commission=0.001)

        self.log(f'Starting Portfolio Value: {self.cerebro.broker.getvalue():.2f}')
        self.results = self.cerebro.run()
        self.log(f'Final Portfolio Value: {self.cerebro.broker.getvalue():.2f}')


    def plot(self):
        import warnings
        from bokeh.util.warnings import BokehDeprecationWarning

        warnings.filterwarnings(
            "ignore",
            message=".*circle.*deprecated.*",
            category=BokehDeprecationWarning,
        )

        warnings.filterwarnings(
            "ignore",
            message=".*triangle.*deprecated.*",
            category=BokehDeprecationWarning,
        )

        btp = BacktraderPlotting(
            scheme=Tradimo(),
            numfigs=1
        )
        self.cerebro.plot(btp)
