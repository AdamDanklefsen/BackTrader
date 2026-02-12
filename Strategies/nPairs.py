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
        self.plotinfo.plotyhlines = [-1, 0, 1] # Should fix to use entry and exit params
        self.plotinfo.plotymargin = .3

class Pair():
    def __init__(self, TickerA, TickerB, last_beta_rebalance, last_phi_rebalance):
        self.TickerA = TickerA
        self.TickerB = TickerB
        self.last_beta_rebalance = last_beta_rebalance
        self.last_phi_rebalance = last_phi_rebalance
        
        self.alpha = None
        self.beta = None
        self.alphas = []
        self.betas = []
        self.pending_alpha = None
        self.pending_beta = None
        self.pending_alphas = []
        self.pending_betas = []
        

        self.AR1 = None
        self.AR1s = []

        self.corr = None
        self.corrs = []


        self.cointegration_tstat = None

    def update_params(self, dt):
        self.alpha = self.pending_alpha
        self.beta = self.pending_beta
        self.alphas.append((dt, self.alpha))
        self.betas.append((dt, self.beta))
        self.pending_alpha = None
        self.pending_beta = None
    def set_pending_params(self, alpha, beta, dt):
        self.pending_alpha = alpha
        self.pending_beta = beta
        self.pending_alphas.append((dt, alpha))
        self.pending_betas.append((dt, beta))

    def update_AR1(self, AR1, dt):
        self.AR1 = AR1
        self.AR1s.append((dt, AR1))

    def plot_params(self):
        import matplotlib.pyplot as plt
        plt.subplots(4,1, figsize=(12, 6))

        if self.alphas:
            dates, alpha_values = zip(*self.alphas)
            plt.subplot(4,1,1)
            plt.plot(dates, alpha_values, marker='o')
            plt.title(f'Alpha over Time for Pair {self.TickerA}, {self.TickerB}')
            plt.xlabel('Date')
            plt.ylabel('Alpha')
            plt.grid()

        if self.betas:
            dates, beta_values = zip(*self.betas)
            plt.subplot(4,1,2)
            plt.plot(dates, beta_values, marker='o', color='orange')
            plt.title(f'Beta over Time for Pair {self.TickerA}, {self.TickerB}')
            plt.xlabel('Date')
            plt.ylabel('Beta')
            plt.grid()

        if self.AR1s:
            dates, AR1_values = zip(*self.AR1s)
            plt.subplot(4,1,3)
            plt.plot(dates, -np.log(2) / np.log(AR1_values), marker='o', color='green')
            plt.title(f'Half-Life of MR over Time for Pair {self.TickerA}, {self.TickerB}')
            plt.xlabel('Date')
            plt.ylabel('Half-Life')
            plt.ylim(0, 20)
            plt.grid()

        if self.corrs:
            dates, corr_values = zip(*self.corrs)
            plt.subplot(4,1,4)
            plt.plot(dates, corr_values, marker='o', color='red')
            plt.title(f'Correlation over Time for Pair {self.TickerA}, {self.TickerB}')
            plt.xlabel('Date')
            plt.ylabel('Correlation')
            plt.grid()
        plt.show()




class nPairsStrategy(bt.Strategy):
    params = (
        ('nSecurities', 4),
        ('entry', 1.0),
        ('exit', 0.01),
        ('beta_rebalance_period', None),
        ('beta_initial_dead_time', None),
        ('phi_rebalance_period', None),
        ('phi_initial_dead_time', None),
        ('start_date', None),
        ('verbose', False),
    )

    def log(self, txt, dt=None):
        if self.verbose:
            if dt is not None:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(f'{txt}')

    def __init__(self):
        self.verbose = self.params.verbose
        self.log("Initializing PairsStrategy...")
        self.pairs = {}
        self.start_date = self.params.start_date
        

        for i in range(self.params.nSecurities):
            for j in range(i + 1, self.params.nSecurities):
                self.log(f"Setting up pair: {i}, {j}")
                pair_key = (i, j)
                self.pairs[pair_key] = Pair(TickerA=self.datas[i]._name, TickerB=self.datas[j]._name,
                                            last_beta_rebalance=self.start_date, last_phi_rebalance=self.start_date)
                

    def stop(self):
        for pair_key, pair in self.pairs.items():
            pair.plot_params()




    def next(self):
        dt = self.datas[0].datetime.date(0)
        cash = self.broker.get_cash()/2.1
        for i in range(self.params.nSecurities):
            for j in range(i + 1, self.params.nSecurities):
                pair_key = (i, j)
                pair = self.pairs[pair_key]
                posA = self.getposition(self.datas[i])
                posB = self.getposition(self.datas[j])
                if not posA.size and not posB.size:
                    # Check entry conditions
                    pass
                else:
                    # Check exit conditions
                    pass
                
                # print(f"Checking dt: {dt} >= {pair.last_beta_rebalance} + {self.params.beta_rebalance_period} and dt >= {self.start_date} + {self.params.beta_initial_dead_time}")
                if dt >= pair.last_beta_rebalance + self.params.beta_rebalance_period and dt >= self.start_date + self.params.beta_initial_dead_time:  # Quarterly rebalance
                    pair.corr = np.corrcoef(np.log(np.array([self.datas[i].close[k] for k in range(-252*2, 0)])),
                                            np.log(np.array([self.datas[j].close[k] for k in range(-252*2, 0)])))[0, 1]
                    pair.corrs.append((dt, pair.corr))
                    pair.last_beta_rebalance = dt
                    print(f"Rebalancing beta for pair {pair.TickerA}, {pair.TickerB} at {dt}")
                    # Recalculate beta
                    A_close = np.log(np.array([self.datas[i].close[k] for k in range(-252*2, 0)]))
                    B_close = np.log(np.array([self.datas[j].close[k] for k in range(-252*2, 0)]))
                    B_close = sm.add_constant(B_close)
                    alpha, beta = sm.OLS(A_close, B_close).fit().params
                    pair.set_pending_params(alpha, beta, dt)
                    # Apply pending params if not in position
                    if not posA.size and not posB.size:
                        pair.update_params(dt)
                        self.log(f"Updated alpha: {pair.alpha:.4f}, beta: {pair.beta:.4f} for pair {pair.TickerA}, {pair.TickerB} at {dt}")
                    pass

                if dt >= pair.last_phi_rebalance + self.params.phi_rebalance_period and dt >= self.start_date + self.params.phi_initial_dead_time:
                    if pair.beta is None or pair.alpha is None:
                        continue  # Cannot rebalance phi without beta and alpha
                    pair.last_phi_rebalance = dt
                    print(f"Rebalancing phi for pair {pair.TickerA}, {pair.TickerB} at {dt}")
                    # Recalculate AR(1) coefficient
                    A_close = np.log(np.array([self.datas[i].close[k] for k in range(-252, 0)]))
                    B_close = np.log(np.array([self.datas[j].close[k] for k in range(-252, 0)]))
                    spread = A_close - (pair.beta * B_close + pair.alpha)
                    spread_lagged = spread[:-1]
                    spread_current = spread[1:]
                    AR1 = sm.OLS(spread_current, sm.add_constant(spread_lagged)).fit().params[1]
                    pair.update_AR1(AR1, dt)
                    self.log(f"Updated AR(1): {pair.AR1:.4f} for pair {pair.TickerA}, {pair.TickerB} at {dt}")
                    pass
