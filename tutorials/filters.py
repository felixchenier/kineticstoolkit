# %%
"""
filters
=======
This module wraps some filters to use directly with ktk's TimeSeries object.
These filters are convenience wrappers for scipy's filters.
"""
import ktk
import numpy as np

# %%
"""
Savitzky-Golay Filter
---------------------
This filter applies the `scipy.signal.savgol_filter` filter to a TimeSeries.
"""
help(ktk.filters.savgol)

# %%
"""
Let define a TimeSeries were data1 is time^2 and data2 is time^4.
"""
time = np.linspace(0, 1, 100)

tsin = ktk.TimeSeries(time=time)
tsin.data['data1'] = time**2
tsin.data['data2'] = time**4

# %%
"""
Using `ktk.filters.savgol`, we can smooth or derivate these data.

Smooth:
"""
y = ktk.filters.savgol(tsin, 3, 2, 0)
y.plot()

# %%
"""
1st derivative:
"""
doty = ktk.filters.savgol(tsin, 3, 2, 1)
doty.plot()

# %%
"""
2nd derivative:
"""
ddoty = ktk.filters.savgol(tsin, 3, 2, 2)
ddoty.plot()

# %% exclude

# TODO Check why I need such a poor tolerance
tol = 5E-3  # Numerical tolerance

assert np.max(np.abs(y.data['data1'][1:-2] - time[1:-2]**2)) < tol
assert np.max(np.abs(doty.data['data1'][1:-2] - 2*time[1:-2])) < tol
assert np.max(np.abs(ddoty.data['data1'][1:-2] - 2)) < tol
assert np.max(np.abs(y.data['data2'][1:-2] - time[1:-2]**4)) < tol
assert np.max(np.abs(doty.data['data2'][1:-2] - 4*(time[1:-2]**3))) < tol
assert np.max(np.abs(ddoty.data['data2'][1:-2] - 12*time[1:-2]**2)) < tol

# Test if it still works with nans in data
tsin.data['data2'][0] = np.nan

y = ktk.filters.savgol(tsin, 3, 2, 0)
doty = ktk.filters.savgol(tsin, 3, 2, 1)
ddoty = ktk.filters.savgol(tsin, 3, 2, 2)

y.data['data2'][0] = np.nan
y.data['data2'][-1] = np.nan
tokeep = ~np.isnan(y.data['data2'])
#tokeep = np.nonzero(tokeep)

assert np.max(np.abs(y.data['data1'][tokeep] - time[tokeep]**2)) < tol
assert np.max(np.abs(doty.data['data1'][tokeep] - 2*time[tokeep])) < tol
assert np.max(np.abs(ddoty.data['data1'][tokeep] - 2)) < tol
assert np.max(np.abs(y.data['data2'][tokeep] - time[tokeep]**4)) < tol
assert np.max(np.abs(doty.data['data2'][tokeep] -
                     4*(time[tokeep]**3))) < tol
assert np.max(np.abs(ddoty.data['data2'][tokeep] -
                     12*time[tokeep]**2)) < tol

# %%
"""
Smooth Filter
-------------
The smooth filter `ktk.smooth` is a convenience function that smooths a
TimeSeries using a moving average of N samples. It calls the Savitzky-Golay
filter with a polynom order of 0.
"""
help(ktk.filters.smooth)

# %%
"""
Let define a TimeSeries with some data inside:
"""
data = np.array(
        [0.7060, 0.0318, 0.2769, 0.0462, 0.0971, 0.8235, 0.6948,
         0.3171, 0.9502, 0.0344, 0.4387, 0.3816, 0.7655, 0.7952,
         0.1869, 0.4898, 0.4456, 0.6463, 0.7094, 0.7547, 0.2760,
         0.6797, 0.6551, 0.1626, 0.1190, 0.4984, 0.9597, 0.3404,
         0.5853, 0.2238])

ts = ktk.TimeSeries()
ts.data['data'] = data
ts.time = np.linspace(0, 1, len(data))

ts.plot()

# %%
"""
Now we smooth this function using a moving average on 5 samples.
"""
y = ktk.filters.smooth(ts, 5)
y.plot()

# %% exclude
tol = 1E-10  # Numerical tolerance

# Test that if filters well
assert np.abs(np.mean(ts.data['data'][4:8] - y.data['data'][6] < tol))

# Test if it filters at all
assert np.abs(np.mean(ts.data['data'][6] - y.data['data'][6] > tol))

# Test if it works with nan
ts.data['data'][9] = np.nan
y = ktk.filters.smooth(ts, 5)
# Test that if filters well
assert np.abs(np.mean(ts.data['data'][4:8] - y.data['data'][6] < tol))
# Test if it filters at all
assert np.abs(np.mean(ts.data['data'][6] - y.data['data'][6] > tol))
