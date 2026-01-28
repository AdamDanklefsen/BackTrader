import backtrader as bt


class SMA(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', False),
    )
    def log(self, txt, dt=None, doprint=False):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog or doprint:
            print('%s, %s' % (dt.isoformat(), txt))
    def __init__(self):
        self.dataclose = self.datas[0].close

        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        
        # # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0]).plot = False
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
    
    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        if self.order:
            return

        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
    
    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)
        
    def build_results_df(self, results):
        import pandas as pd
        strats = [x[0] for x in results]

        results_list = []
        for i, strat in enumerate(strats):
            r_annual = strat.analyzers.annualizedreturn.get_analysis()['annualizedreturn']
            sharpe = strat.analyzers.sharpe.get_analysis()['sharperatio']
            drawdown = strat.analyzers.drawdown.get_analysis()['max']['drawdown']
            vol = strat.analyzers.annualizedvolatility.get_analysis()['volatility']
            results_list.append({
                'Strategy': i,
                'MA Period': strat.params.maperiod,
                'Annualized Return': r_annual,
                'Sharpe Ratio': sharpe,
                'Max Drawdown': drawdown,
                'Annualized Volatility': vol
            })

        resultsDF = pd.DataFrame(results_list)
        self.resultsDF = resultsDF
        return resultsDF
    
    def plot_frontier(self):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10,6))
        plt.scatter(self.resultsDF['Annualized Volatility'], self.resultsDF['Annualized Return'])
        plt.xlabel('Annualized Volatility')
        plt.ylabel('Annualized Return')
        plt.title('Annualized Return vs Annualized Volatility')
        plt.show()

    def plot_sharpe(self):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10,6))
        plt.plot(self.resultsDF['MA Period'], self.resultsDF['Sharpe Ratio'], label='Sharpe Ratio')
        plt.xlabel('MA Period')
        plt.ylabel('Sharpe Ratio')
        plt.title('Sharpe Ratio vs MA Period')
        plt.legend()
        plt.show()

    def plot_sharpe_vs_MAperiod(self):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10,6))
        plt.plot(self.resultsDF['MA Period'], self.resultsDF['Sharpe Ratio'], label='Sharpe Ratio')
        plt.xlabel('MA Period')
        plt.ylabel('Sharpe Ratio')
        plt.title('Sharpe Ratio vs MA Period')
        plt.legend()
        plt.show()