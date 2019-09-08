#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 13:29:24 2019

@author: felix
"""

import ktk
import scipy.io as _spio
import os as _os
import subprocess as _subprocess


def loadmat(filename):
    """
    Load a Matlab's MAT file.
    """
    # The MAT file should first be converted using Matlab's own runtime
    # engine, so that Matlab's timeseries are converted to structures.
    converted_filename = ktk.config['RootFolder'] + '/loadsave_converted.mat'

    if ktk.config['IsMac']:
        script_name = '/external/ktkMATtoPython/run_ktkMATtoPython.sh'
        runtime_path = '/Applications/MATLAB/MATLAB_Runtime/v91/'
    else:
        raise(NotImplementedError('loadmat is only available on Mac for now.'))

    _subprocess.run([ktk.config['RootFolder'] + script_name, runtime_path,
                      filename, converted_filename],
                      stderr=_subprocess.DEVNULL,
                      stdout=_subprocess.DEVNULL)

    # Now load it with scipy.io then delete file
    data = _spio.loadmat(converted_filename, struct_as_record=False,
                         squeeze_me=True)
    _os.remove(converted_filename)


    # Correct the keys
    data = _check_keys(data)

    # Assign contents to data
    data = data['contents']

    return data



def convert_to_timeseries(the_input):

    if isinstance(the_input, dict):
#c        print("This is a dict. Checking if it's a timeseries.")

        is_a_timeseries = False

        for the_key in the_input.keys():

            if isinstance(the_input[the_key], dict):
                if 'type' in the_input[the_key].keys():
                    if the_input[the_key]['type'] == 'timeseries':
                        is_a_timeseries = True
#                    else:
#                        is_a_timeseries = False
#                else:
#                    is_a_timeseries = False
#            else:
#                is_a_timeseries = False
        # end for the_key


        if is_a_timeseries == True:
            #After checking if each key is a timeseries, and it is, we get here.
            the_output = ktk.TimeSeries()
            for the_key in the_input.keys():
                try:
                    the_output.time = the_input[the_key]['Time']
                    the_data = the_input[the_key]['Data']
                    the_shape = the_data.shape
                    if len(the_shape) == 2:
                        the_output.data[the_key] = the_data.transpose((1,0))
                    elif len(the_shape) == 3:
                        the_output.data[the_key] = the_data.transpose((2,0,1))
                    else:
                        the_output.data[the_key] = the_data

                except:
                    pass

            return the_output
        else:
            print('This was not a timeseries.')

            for the_key in the_input.keys():
                print('  Now processing key %s' % the_key)
                the_input[the_key] = convert_to_timeseries(the_input[the_key])
            return the_input

    else:
        return the_input




def _check_keys(dict):
    '''
    checks if entries in dictionary are mat-objects. If yes
    todict is called to change them to nested dictionaries
    '''
    for key in dict:
        if isinstance(dict[key], _spio.matlab.mio5_params.mat_struct):
            dict[key] = _todict(dict[key])
    return dict

def _todict(matobj):
    '''
    A recursive function which constructs from matobjects nested dictionaries
    '''
    dict = {}
    for strg in matobj._fieldnames:
        elem = matobj.__dict__[strg]
        if isinstance(elem, _spio.matlab.mio5_params.mat_struct):
            dict[strg] = _todict(elem)
        else:
            dict[strg] = elem
    return dict
