#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from backtrader.utils.py3 import itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import standarddev
from backtrader.analyzers import TimeReturn


class AnnualizedVolatility(Analyzer):
    '''This analyzer calculates the annualized volatility of a strategy using
    the standard deviation of returns

    Params:

      - ``timeframe``: (default: ``TimeFrame.Years``)

      - ``compression`` (default: ``1``)

        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression

      - ``factor`` (default: ``None``)

        If ``None``, the annualization factor will be chosen from a predefined
        table based on the timeframe

          Days: 252, Weeks: 52, Months: 12, Years: 1

        Else the specified value will be used

      - ``annualize`` (default: ``True``)

        If ``True``, the volatility will be annualized by multiplying by
        sqrt(factor). If ``False``, returns the volatility in the chosen
        timeframe without annualization

      - ``stddev_sample`` (default: ``False``)

        If this is set to ``True`` the *standard deviation* will be calculated
        decreasing the denominator in the mean by ``1``. This is used when
        calculating the *standard deviation* if it's considered that not all
        samples are used for the calculation. This is known as the *Bessels'
        correction*

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with key "volatility" holding the annualized
        volatility value

    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('factor', None),
        ('annualize', True),
        ('stddev_sample', False),
        ('fund', None),
    )

    RATEFACTORS = {
        TimeFrame.Days: 252,
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

    def __init__(self):
        self.timereturn = TimeReturn(
            timeframe=self.p.timeframe,
            compression=self.p.compression,
            fund=self.p.fund)

    def stop(self):
        super(AnnualizedVolatility, self).stop()
        # Get the returns from the subanalyzer
        returns = list(itervalues(self.timereturn.get_analysis()))

        factor = None

        if self.p.factor is not None:
            factor = self.p.factor  # user specified factor
        elif self.p.timeframe in self.RATEFACTORS:
            # Get the conversion factor from the default table
            factor = self.RATEFACTORS[self.p.timeframe]

        lrets = len(returns) - self.p.stddev_sample
        # Check if the volatility can be calculated
        if lrets:
            retdev = standarddev(returns, bessel=self.p.stddev_sample)

            try:
                if factor is not None and self.p.annualize:
                    # Annualize the volatility
                    volatility = retdev * math.sqrt(factor)
                else:
                    # Return volatility in the chosen timeframe
                    volatility = retdev
            except (ValueError, TypeError, ZeroDivisionError):
                volatility = None
        else:
            # no returns or stddev_sample was active and 1 return
            volatility = None

        self.rets['volatility'] = volatility