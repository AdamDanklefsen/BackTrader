import backtrader as bt

def addAnalyzersList(cerebro):
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, compression=1, riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')
    from analyzers.anualizedvolatility import AnnualizedVolatility
    cerebro.addanalyzer(AnnualizedVolatility, _name='annualizedvolatility', timeframe=bt.TimeFrame.Days)
    from analyzers.annualizedReturn import AnnualizedReturn
    cerebro.addanalyzer(AnnualizedReturn, _name='annualizedreturn', timeframe=bt.TimeFrame.Days)