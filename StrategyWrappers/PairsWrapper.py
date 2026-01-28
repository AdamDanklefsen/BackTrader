import backtrader as bt
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import numpy as np
import pandas as pd

import yfinance as yf

from btplotting import BacktraderPlotting
from btplotting.schemes import Tradimo


class PairsWrapper():
    def log(self, txt, dt=None):
        if self.verbose:
            if dt is not None:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(f'{txt}')

    def __init__(self, start_Date, end_date, TickerA, TickerB, verbose=False, entry=1.0, exit=0.01):
        self.start_Date = start_Date
        self.end_date = end_date
        self.TickerA = TickerA
        self.TickerB = TickerB
        self.verbose = verbose
        self.entry = entry
        self.exit = exit



        self.A = yf.download(self.TickerA, self.start_Date, self.end_date).xs(self.TickerA, level='Ticker', axis=1, drop_level=True)
        self.B = yf.download(self.TickerB, self.start_Date, self.end_date).xs(self.TickerB, level='Ticker', axis=1, drop_level=True)
        self.log(f"Downloaded data for {self.TickerA}  from {self.A.index[0]} to {self.A.index[-1]}")
        self.log(f"Downloaded data for {self.TickerB}  from {self.B.index[0]} to {self.B.index[-1]}")
        self.dataA = bt.feeds.PandasData(dataname=self.A, name=self.TickerA)
        self.dataB = bt.feeds.PandasData(dataname=self.B, name=self.TickerB)

        self.alpha, self.beta = sm.OLS(
            np.log(self.A['Close']),
            sm.add_constant(np.log(self.B['Close']))
        ).fit().params
        self.log(f"Alpha: {self.alpha:.4f}, Beta: {self.beta:.4f}")

        cointegration_test = coint(
            np.log(self.A['Close']),
            np.log(self.B['Close'])
        )
        self.log(f"Cointegration test p-value: {cointegration_test[1]:.4f} {'>' if cointegration_test[1] > 0.05 else '<='} 0.05 {'(Not Cointegrated)' if cointegration_test[1] > 0.05 else '(Cointegrated)'}")

        self.cerebro = bt.Cerebro()
        self.cerebro.adddata(self.dataA)
        self.cerebro.adddata(self.dataB)
        from Strategies.Pairs import PairsStrategy, PairPnlAnalyzer
        self.cerebro.addstrategy(
            PairsStrategy,
            entry=self.entry,
            exit=self.exit,
            alpha=self.alpha,
            beta=self.beta,
            verbose=self.verbose
        )

        self.cerebro.addanalyzer(PairPnlAnalyzer, _name='pairpnl')
        import analyzers.addAnalyzersList
        analyzers.addAnalyzersList.addAnalyzersList(self.cerebro)

        self.cerebro.broker.setcash(100000.0)
        self.cerebro.broker.setcommission(commission=0.001)

        self.log('Starting Portfolio Value: %.2f' % self.cerebro.broker.getvalue())
        self.results = self.cerebro.run()
        self.log('Final Portfolio Value: %.2f' % self.cerebro.broker.getvalue())

        pairpnl = self.results[0].analyzers.pairpnl.get_analysis()
        dates = self.A.index[-len(pairpnl):]
        self.pairpnl_series = pd.Series(pairpnl, index=dates, name='Pair PnL')

        Sharpe = self.results[0].analyzers.sharpe.get_analysis()['sharperatio']
        AnnualizedReturn = self.results[0].analyzers.annualizedreturn.get_analysis()['annualizedreturn']
        MaxDrawdown = self.results[0].analyzers.drawdown.get_analysis()['max']['drawdown']
        MaxDrawdownLen = self.results[0].analyzers.drawdown.get_analysis()['max']['len']

        print(f"Pairs Strategy Sharpe Ratio: {Sharpe:.4f}")
        print(f"Pairs Strategy Annualized Return: {AnnualizedReturn:.4%}")
        print(f"Pairs Strategy Max Drawdown: {MaxDrawdown:.4%}")
        print(f"Pairs Strategy Max Drawdown Length: {MaxDrawdownLen} days")
    

    def plot_pair(self):
        import mplfinance as mpf

        adp = [
            mpf.make_addplot(self.A['Close'], panel=0, color='blue', ylabel=self.TickerA),
            mpf.make_addplot(self.B['Close'], panel=0, color='orange', ylabel=self.TickerB, secondary_y=True)
        ]

        fig, axs = mpf.plot(self.A,
                            type='line',
                            addplot=adp,
                            style='yahoo',
                            title=f'{self.TickerA} and {self.TickerB} Prices',
                            volume=False,
                            returnfig=True)

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


    def plot_pnl(self):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.plot(self.pairpnl_series, label='Pair PnL', color='purple')
        plt.title(f'Pair PnL for {self.TickerA} and {self.TickerB}')
        plt.xlabel('Date')
        plt.ylabel('PnL')
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.legend()
        plt.grid()
        plt.show()