import backtrader as bt
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
import numpy as np

import math
class Log(bt.Indicator):
    lines = ('log',)

    def __init__(self):
        self.plotinfo.subplot = False
        self.plotinfo.plot = False

    def next(self):
        self.lines.log[0] = math.log(self.data[0])

class NormalizedSpread(bt.Indicator):
    lines = ('normSpread',)
    params = (
        ('period', 252),
        ('alpha', None),
        ('beta', None),
    )

    def __init__(self):
        A = Log(self.datas[0].close)
        B = Log(self.datas[1].close)
        self.addminperiod(self.params.period)

        print(f"NormalizedSpread alpha: {self.params.alpha}, beta: {self.params.beta}")

        self.spread = A - (self.params.beta * B + self.params.alpha)
        mean = bt.ind.EMA(self.spread, period=self.params.period)
        stddev = bt.ind.StdDev(self.spread, period=self.params.period)

        self.lines.normSpread = (self.spread) / stddev
        # self.lines.normSpread = (self.spread - mean) / stddev

        self.plotinfo.subplot = True
        self.plotinfo.plotname = 'Normalized Spread'
        self.plotinfo.plotyhlines = [-1, 0, 1]
        self.plotinfo.plotymargin = .3


class PairPnlAnalyzer(bt.Analyzer):
    def start(self):
        self.pnls = []
    def next(self):
        posA = self.strategy.getposition(self.strategy.datas[0])
        posB = self.strategy.getposition(self.strategy.datas[1])

        pnlA = (self.strategy.datas[0].close[0] - posA.price) * posA.size
        pnlB = (self.strategy.datas[1].close[0] - posB.price) * posB.size

        self.pnls.append(pnlA + pnlB)
    def get_analysis(self):
        return self.pnls
    

class PairsStrategy(bt.Strategy):
    params = (
        ('entry', 1.0),
        ('exit', 0.1),
        ('alpha', None),
        ('beta', None),
        ('verbose', False),
    )

    def log(self, txt, dt=None):
        if self.verbose:
            if dt is not None:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(f'{txt}')


    def __init__(self):
        self.A = self.datas[0]
        self.B = self.datas[1]
        self.in_trade = False
        self.verbose = self.params.verbose


        self.A_Close_log = Log(self.A.close)
        self.B_Close_log = Log(self.B.close)
        self.log("Fitting OLS model for cointegration...")


        self.spread = self.A_Close_log - (self.params.beta * self.B_Close_log + self.params.alpha)

        self.zscore = NormalizedSpread(self.A, self.B, alpha=self.params.alpha, beta=self.params.beta, period=252)

    def next(self):
        dt = self.datas[0].datetime.datetime(0)
        cash = self.broker.get_cash()/2.1
        posA = self.getposition(self.A)
        posB = self.getposition(self.B)
        if not posA.size and not posB.size:
            if self.zscore[0] > self.params.entry:
                short = np.round(cash / self.A.close[0], 0)
                long = np.round(self.params.beta * cash / self.B.close[0], 0)
                self.log(f"{dt} - Shorting {short} shares of A and buying {long} shares of B")

                self.sell(data=self.A, size = short)
                self.buy(data=self.B, size = long)
            elif self.zscore[0] < -self.params.entry:
                short = np.round(self.params.beta * cash / self.B.close[0], 0)
                long = np.round(cash / self.A.close[0], 0)
                self.log(f"{dt} - Buying {long} shares of A and shorting {short} shares of B")

                self.buy(data=self.A, size = long)
                self.sell(data=self.B, size = short)
            else:
                # self.log(f"{dt} - No trade signal. Z-score: {self.zscore[0]:.4f}")
                pass
        elif posA.size != 0 and posB.size != 0:
            if abs(self.zscore[0]) < self.params.exit or self.zscore[0] * self.zscore[-1] < 0: # sign change
                self.log(f"{dt} - Closing {posA.size} shares of A and {posB.size} shares of B")
                self.close(data=self.A)
                self.close(data=self.B)
            elif (self.A.close[0] - posA.price) * posA.size + (self.B.close[0] - posB.price) * posB.size < -cash * .05:
                self.log(f"{dt} - Stop loss triggered. Closing {posA.size} shares of A and {posB.size} shares of B")
                self.close(data=self.A)
                self.close(data=self.B)
            else:
                # self.log(f"{dt} - Holding positions. Z-score: {self.zscore[0]:.4f}")
                pass
        else:
            self.log(f"{dt} - Warning: Inconsistent positions detected. Positions - A: {posA.size}, B: {posB.size}")


