import backtrader as bt
import fracdiff as fd
import pyvinecopulib as pv
import numpy as np


#fractional differencing indicator
class fdiff(bt.Indicator):
    lines = ('fdiff',)
    params = (('d', 0.5),)

    

    def __init__(self):
        self.plotinfo.subplot = False
        self.plotinfo.plot = False

        weights = fd.get_weights_by_threshold(self.params.d, threshold=1e-4)
        self.weights = weights
        self.max_lag = len(weights) - 1

        self.plotinfo.subplot = True
        self.plotinfo.plot = True
        self.plotinfo.plotname = f'FracDiff d={self.params.d}'
        self.plotinfo.plotymargin = .3


    def next(self):
        val = 0.0
        if len(self.datas[0]) <= self.max_lag:
            self.lines.fdiff[0] = float('nan')
            return
        else:
            for k in range(self.max_lag + 1):
                val += self.weights[k] * self.datas[0].close[-k]
            self.lines.fdiff[0] = val


# MPI indicator
class MPI(bt.Indicator):
    pass



class PCFracStrategy(bt.Strategy):
    params = (
        ('Nsecurities', 2),
        ('d', .5),
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
        self.log("Initializing PCFracStrategy...")
        self.A = self.datas[0]
        self.B = self.datas[1]

        self.A_fd = fdiff(self.A, d=self.params.d)
        self.B_fd = fdiff(self.B, d=self.params.d)

        
        


        

        self.verbose = self.params.verbose