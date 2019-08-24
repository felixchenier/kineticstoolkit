#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply standard filters on TimeSeries.

Author: Félix Chénier
Started on Aug 1st, 2019.
"""

import numpy as np
import scipy as sp
import scipy.signal as sgl
import warnings


def savgol(tsin, window_length, poly_order, deriv=0):
    """
    Apply a Savitzky-Golay filter on a TimeSeries.

    Parameters
    ----------
    tsin : ktk.TimeSeries
        Input TimeSeries
    window_length : int
        The length of the filter window. window_length must be a positive
        odd integer less or equal than the length of the TimeSeries.
    poly_order : int
        The order of the polynomial used to fit the samples. polyorder must be
        less than window_length.
    deriv : int, optional
        The order of the derivative to compute. This must be a nonnegative
        integer. The default is 0, which means to filter the data without
        differentiating.

    Returns
    -------
    tsout : ktk.TimeSeries
        The filtered TimeSeries

    The input timeseries must contain no missing samples. If missing samples
    are found, a warning is issued, missing samples are interpolated using a
    first-order interpolation before filtering, and then replaced by NaNs in
    the filtered signal.

    """
    tsout = tsin.copy()

    delta = tsin.time[1] - tsin.time[0]

    for key in tsout.data.keys():

        input_signal = tsout.data[key]
        # Resample NaNs if the exist:

        # Find NaNs
        signal_shape = np.shape(input_signal)

        n_data = signal_shape[0]
        each_data_shape = signal_shape[1:]

        n_data = np.shape(input_signal)[0]
        nan_index = np.isnan(np.sum(input_signal, axis=each_data_shape))

        if len(np.nonzero(nan_index)) > 0:
            # There were NaNs, issue a warning.
            warnings.warn('NaNs found in the signal. They have been ' +
                          'interpolated before filtering, and then put back ' +
                          'in the filtered data')

        original_x = np.arange(n_data)[~nan_index]
        original_y = input_signal[~nan_index]
        new_x = np.arange(n_data)

        # Resample
        input_signal = sp.interp(new_x, original_x, original_y)

        # Filter
        filtered_data = sgl.savgol_filter(input_signal,
                                          window_length, poly_order, deriv,
                                          delta=delta)

        # Put back NaNs
        filtered_data[nan_index] = np.nan

        # Assign it to the output
        tsout.data[key] = filtered_data

    return tsout


def smooth(tsin, window_length):
    """
    Apply a smoothing (moving average) filter on a TimeSeries.

    Parameters
    ----------
    tsin : ktk.TimeSeries
        Input TimeSeries
    window_length : int
        The length of the filter window. window_length must be a positive
        odd integer less or equal than the length of the TimeSeries.

    Returns
    -------
    tsout : ktk.TimeSeries
        The filtered TimeSeries

    """
    tsout = savgol(tsin, window_length, 0)
    return tsout
