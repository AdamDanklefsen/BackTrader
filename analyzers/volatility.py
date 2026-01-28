from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import operator

from backtrader.utils.py3 import map
from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import standarddev


class Volatility(Analyzer):

    def __init__(self):
        super(Volatility, self).__init__()
        self.rets = []
        self.prev_value = None

    def start(self):
        self.prev_value = self.strategy.broker.getvalue()

    def next(self):
        current_value = self.strategy.broker.getvalue()
        if self.prev_value:
            ret = (current_value / self.prev_value) - 1.0
            self.rets.append(ret)
        self.prev_value = current_value

    def stop(self):
        self.retdev = standarddev(self.rets) if self.rets else 0.0

    def get_analysis(self):
        return dict(volatility=self.retdev)