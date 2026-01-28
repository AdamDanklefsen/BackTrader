#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math

from backtrader.utils.py3 import itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.analyzers import TimeReturn


class AnnualizedReturn(Analyzer):
    '''This analyzer calculates the annualized return of a strategy by
    compounding returns over time

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

        If ``True``, the return will be annualized by compounding with
        the appropriate factor. If ``False``, returns the geometric mean
        return in the chosen timeframe without annualization

      - ``fund`` (default: ``None``)

        If ``None`` the actual mode of the broker (fundmode - True/False) will
        be autodetected to decide if the returns are based on the total net
        asset value or on the fund value. See ``set_fundmode`` in the broker
        documentation

        Set it to ``True`` or ``False`` for a specific behavior

    Methods:

      - get_analysis

        Returns a dictionary with key "annualizedreturn" holding the annualized
        return value

    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('factor', None),
        ('annualize', True),
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
        super(AnnualizedReturn, self).stop()
        # Get the returns from the subanalyzer
        returns = list(itervalues(self.timereturn.get_analysis()))

        factor = None

        if self.p.factor is not None:
            factor = self.p.factor  # user specified factor
        elif self.p.timeframe in self.RATEFACTORS:
            # Get the conversion factor from the default table
            factor = self.RATEFACTORS[self.p.timeframe]

        # Check if we have returns to calculate
        if returns:
            # Calculate compound/geometric return
            total_return = 1.0
            for ret in returns:
                total_return *= (1.0 + ret)
            
            # Geometric mean return per period
            num_periods = len(returns)
            geometric_mean = math.pow(total_return, 1.0 / num_periods) - 1.0

            try:
                if factor is not None and self.p.annualize:
                    # Annualize the return by compounding over the factor
                    annualized_return = math.pow(1.0 + geometric_mean, factor) - 1.0
                else:
                    # Return the geometric mean in the chosen timeframe
                    annualized_return = geometric_mean
            except (ValueError, TypeError, ZeroDivisionError):
                annualized_return = None
        else:
            # no returns available
            annualized_return = None

        self.rets['annualizedreturn'] = annualized_return