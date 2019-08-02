#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KTK development functions.

Author: Félix Chénier
Date: July 2019
"""

import subprocess
from ktk import _ROOT_FOLDER
import webbrowser

import unittest
from .unittests.timeseries import timeseriesTest
from .unittests.loadsave import loadsaveTest
from .unittests.pushrimkinetics import pushrimkineticsTest
from .unittests.filters import filtersTest



def run_tests():
    """Run all unit tests."""
    suite = unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(timeseriesTest),
            unittest.TestLoader().loadTestsFromTestCase(loadsaveTest),
            unittest.TestLoader().loadTestsFromTestCase(pushrimkineticsTest),
            unittest.TestLoader().loadTestsFromTestCase(filtersTest)
            ])
    unittest.TextTestRunner(verbosity=2).run(suite)

def generate_tutorials():
    """Update the Jupyter tutorials into their final html form."""
    subprocess.call(['jupyter-nbconvert', '--to=html', '--execute',
                         _ROOT_FOLDER + '/tutorials/*.ipynb'])
    webbrowser.open('file:///' + _ROOT_FOLDER + '/tutorials/index.html', new=2)

def release():
    run_tests()
    generate_tutorials()
