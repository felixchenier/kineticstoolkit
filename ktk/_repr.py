#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Format the console output of few classes.

This module reformats the console output of dict in ipython, so that instead
of just using __repr__, it displays a nicer list of keys with abbreviated
values if required, so that there is a maximum of one key per line. This is
very useful for nested dicts, since their __repr__ representation is
recursive and becomes unmanagable when the dict becomes larger.

It also formats the output of some data classes such as the classes defined in
dbinterface.

Author: Felix Chenier
Date: July 16th, 2019
felixchenier.com
"""

def _format_dict_entries(value, quotes=True):
    
    if quotes:
        quote_text = "'"
    else:
        quote_text = ""
    
    out = ''
    
    # Find the widest field name
    the_keys = value.keys()
    if len(the_keys) > 0:
        
        the_max_length = 0
        for the_key in the_keys:
            the_max_length = max(the_max_length, len(the_key))
    
        max_length_to_show = 77 - the_max_length
        
        for the_key in the_keys:
            
            # Print the key
            to_show = quote_text + the_key + quote_text
            out += (to_show.rjust(the_max_length+2) + ': ') #+2 for the possible quotes
            
            # Print the value
            try:
                to_show = repr(value[the_key])
            except:
                to_show = ''
                
            to_show = ' '.join(to_show.split()) # Remove line breaks and multiple-spaces
            if len(to_show) <= max_length_to_show:
                out += to_show
            else:
                out += (to_show[0:max_length_to_show-3] + '...')

            # Print the ending } if needed
            out += '\n'

    return out
    
    

def _ktk_format_dict(value, p, cycle):
    """Format a dict nicely on screen in ipython."""
    
    if cycle:
        p.pretty("...")
    else:
        p.text('{\n')
        p.text(_format_dict_entries(value))
        p.text('}')

try:  
    import IPython.lib.pretty as pretty
    
    formatter = get_ipython().display_formatter.formatters['text/plain']
    formatter.for_type(dict, lambda n, p, cycle: _ktk_format_dict(n, p, cycle))

except:
    pass
