import backtrader as bt
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import numpy as np
import pandas as pd
import datetime as dt

import yfinance as yf

from btplotting import BacktraderPlotting
from btplotting.schemes import Tradimo

class nPairsWrapper():
    def log(self, txt, dt=None):
        if self.verbose:
            if dt is not None:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(f'{txt}')

    def __init__(self, start_date, end_date, Tickers, verbose=False, entry=1.0, exit=0.01):
        self.start_date = start_date
        self.end_date = end_date
        self.Tickers = Tickers
        self.nTickers = len(Tickers)
        self.verbose = verbose
        self.entry = entry
        self.exit = exit
        self.beta_rebalance_period = dt.timedelta(days=252/4)  # Quarterly
        self.beta_initial_dead_time = dt.timedelta(days=252*2)  # 2 years
        self.phi_rebalance_period = dt.timedelta(days=252/12)  # Monthly
        self.phi_initial_dead_time = dt.timedelta(days=252)  # 1 year



        self.downloads = [
            yf.download(ticker, self.start_date, self.end_date).xs(ticker, level='Ticker', axis=1, drop_level=True)
            for ticker in self.Tickers
        ]
        for ticker, data in zip(self.Tickers, self.downloads):
            self.log(f"Downloaded data for {ticker}  from {data.index[0]} to {data.index[-1]}")
            if abs(data.index[0] - pd.to_datetime(self.start_date)) > pd.Timedelta(days=3):
                self.log(f"Warning: Data for {ticker} starts later than requested start date {self.start_date}")
            if abs(data.index[-1] - pd.to_datetime(self.end_date)) > pd.Timedelta(days=3):
                self.log(f"Warning: Data for {ticker} ends earlier than requested end date {self.end_date}")
        self.data = [
            bt.feeds.PandasData(dataname=download, name=ticker)
            for download, ticker in zip(self.downloads, self.Tickers)
        ]

        self.cerebro = bt.Cerebro()
        for data_feed in self.data:
            self.cerebro.adddata(data_feed)
        self.cerebro.broker.setcash(100000.0)
        self.cerebro.broker.setcommission(commission=0.001)

        from Strategies.nPairs import nPairsStrategy
        self.cerebro.addstrategy(
            nPairsStrategy,
            nSecurities=self.nTickers,
            entry=self.entry,
            exit=self.exit,
            beta_rebalance_period=self.beta_rebalance_period,
            beta_initial_dead_time=self.beta_initial_dead_time,
            phi_rebalance_period=self.phi_rebalance_period,
            phi_initial_dead_time=self.phi_initial_dead_time,
            start_date=dt.datetime.strptime(self.start_date, "%Y-%m-%d").date(),
            verbose=self.verbose
        )


        self.log(f'Starting Portfolio Value: {self.cerebro.broker.getvalue():.2f}')
        self.results = self.cerebro.run()
        self.log(f'Final Portfolio Value: {self.cerebro.broker.getvalue():.2f}')