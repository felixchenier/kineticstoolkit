#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 20:36:28 2019

@author: felix
"""

from dataclasses import dataclass
from typing import Dict
import ktk.gui as _gui
import ktk._repr as _repr

import requests


@dataclass
class File:
    """File class."""
    dbid: int = 0
    dbfid: str= ''
    description: str = ''
    file_name: str = ''
    def __repr__(self):
        return _repr._format_class_attributes(self)

@dataclass
class Trial:
    """Trial class that contains files."""
    files: Dict[str, File]
    dbid: int = 0
    trial_type: str = ''
    repetition: int = 0
    description: str = ''
    notes: str= ''
    def __repr__(self):
        return _repr._format_class_attributes(self)

@dataclass
class Session:
    """Session class that contains trials."""
    trials: Dict[str, Trial]
    dbid: int = 0
    date: str = ''
    place: str = ''
    repetition: int = 0
    notes: str = ''
    def __repr__(self):
        return _repr._format_class_attributes(self)

@dataclass
class Participant:
    """Participant class that contains sessions."""
    sessions: Dict[str, Session]
    dbid: int = 0
    uid: int = 0
    label: str = ''
    sex: str = ''
    date_of_birth: str = ''
    date_of_injury: str = ''
    dominant_side: str = ''
    pathology: str = ''
    ais: str = ''
    traumatic: str = ''
    def __repr__(self):
        return _repr._format_class_attributes(self)

@dataclass
class Project():
    """Project class that contains participants."""
    participants: Dict[str, Participant]
    dbid: int = 0
    label: str = ''
    def __repr__(self):
        return _repr._format_class_attributes(self)


def fetch_project(project_label, user='', password='', root_folder='',
                  url='https://biomec.uqam.ca'):
    
    # Get username and password of not supplied
    if user == '':
        user, password = _gui.get_credentials()
    
    # Append the relative url to the base url
    url += '/py/pywrapper.php'
    
    # Do the request and executes it    
    result = requests.post(url, data={
                                    'command': 'fetchall',
                                    'projectlabel': project_label,
                                    'username': user,
                                    'password': password}, verify=False)

    content = result.content.decode("iso8859_15")
    global project
    exec(content)
    return project
