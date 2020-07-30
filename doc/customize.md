Customizing
===========

By default, importing ktk changes some defaults in IPython and matplotlib to
get a more 'research' and less 'programming' experience. Please note that this
does not affect anything besides visual representations. This behaviour can be
changed by modifying ktk's configuration (ktk/config.py). In Spyder/IPython:

    >>> import ktk.config
    >>> edit ktk.config

Modification to repr of dictionaries
------------------------------------

In ktk, data are often stored as dictionaries, which can lead to very large
printouts when we simply want to see the dictionary's contents. Importing ktk
changes the repr of dictionaries in IPython so that a summary of the dict's
content is shown, more like the representation of a Matlab struct.

For example, let's create a dummy dictionary:

    >>> import numpy as np
    >>> data = dict()
    >>> data['data1'] = np.arange(30)
    >>> data['data2'] = np.arange(30) ** 2
    >>> data['data3'] = np.arange(30) ** 3

Before importing ktk:

    >>> data
    {'data1': array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
            17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]),
     'data2': array([  0,   1,   4,   9,  16,  25,  36,  49,  64,  81, 100, 121, 144,
            169, 196, 225, 256, 289, 324, 361, 400, 441, 484, 529, 576, 625,
            676, 729, 784, 841]),
     'data3': array([    0,     1,     8,    27,    64,   125,   216,   343,   512,
              729,  1000,  1331,  1728,  2197,  2744,  3375,  4096,  4913,
             5832,  6859,  8000,  9261, 10648, 12167, 13824, 15625, 17576,
            19683, 21952, 24389])}

After importing ktk:

    >>> import ktk
    >>> data
    {
        'data1': <array of shape (30,)>,
        'data2': <array of shape (30,)>,
        'data3': <array of shape (30,)>
    }


Modification to repr of numpy's floats
--------------------------------------

Numpy is set to display floats with floating point precision.


Alternative defaults for matplotlib
-----------------------------------

We assume that most work with figure is interactive, on screen. In that view,
the following modifications are made to default matplotlib figures:

- The standard dpi is changed to 75, which allows for more space to work by
  reducing the font size on screen.

- The standard figure size is changed to [10, 5], which is a little bigger
  than the default and is thus more practical for interactive navigation.

- The default color order is changed to (rgbcmyko) with o being orange. The
  first colors, red, green and blue, are consistent the colours assigned to
  x, y and z in most 3D visualization softwares, and the next colours are
  consistent with Matlab's legacy color order.
