"""
Module that manages the DBInterface class.

Author: Felix Chenier
Date: April 2020
"""

import ktk
import requests
import os
from io import StringIO
import pandas as pd
import warnings


class DBInterface():
    """Interface for Felix Chenier's BIOMEC database."""

    @property
    def participants(self):
        table = self.tables['Participants']['ParticipantLabel']
        return table.drop_duplicates().to_list()

    @property
    def sessions(self):
        table = self.tables['Sessions']['SessionLabel']
        return table.drop_duplicates().to_list()

    @property
    def trials(self):
        table = self.tables['Trials']['TrialLabel']
        return table.drop_duplicates().to_list()

    @property
    def files(self):
        table = self.tables['Files']['FileLabel']
        return table.drop_duplicates().to_list()


    def __init__(self, project_label, user='', password='', root_folder='',
                 url='https://felixchenier.uqam.ca/biomec',
                 filters=dict()):

        # Simple assignations
        self.project_label = project_label
        self.url = url

        # Get username and password if not supplied
        if user == '':
            self.user, self._password = ktk.gui.get_credentials()
        else:
            self.user = user
            self._password = password

        # Assign root folder
        if root_folder == '':
            ktk.gui.message('Please select the folder that contains the '
                            'project data.')
            self.root_folder = ktk.gui.get_folder()
            ktk.gui.message('')
        else:
            self.root_folder = root_folder

        # Assign tables
        self.refresh()


    def __repr__(self):
        s =  f'--------------------------------------------------\n'
        s += 'DBInterface\n'
        s += f'--------------------------------------------------\n'
        s += f'          url: {self.url}\n'
        s += f'         user: {self.user}\n'
        s += f'project_label: {self.project_label}\n'
        s += f'--------------------------------------------------\n'
        s += f'participants:\n'
        s += str(self.participants) + '\n'
        s += f'--------------------------------------------------\n'
        s += f'sessions:\n'
        s += str(self.sessions) + '\n'
        s += f'--------------------------------------------------\n'
        s += f'trials:\n'
        s += str(self.trials) + '\n'
        s += f'--------------------------------------------------\n'
        s += f'files:\n'
        s += str(self.files) + '\n'
        s += f'--------------------------------------------------\n'
        return s


    def _fetch_table(self, table_name):
        global _module_user, _module_password
        url = self.url + '/kineticstoolkit/dbinterface.php'
        result = requests.post(url, data={
            'username': self.user,
            'password': self._password,
            'projectlabel': self.project_label,
            'action': 'fetchtable',
            'table': table_name})

        csv_text = result.content.decode("iso8859_15")
        if '# INVALID USER/PASSWORD COMBINATION' in csv_text:
            raise ValueError('Invalid user/password combination')

        try:
            return pd.read_csv(StringIO(csv_text),
                               comment='#',
                               delimiter='\t')
        except Exception:
            print(csv_text)
            raise ValueError('Unknown exception, see above.')


    def _scan_files(self):

        # Scan all files in root folder
        dict_files = {'FileID': [], 'FileName': []}

        warned_once = False
        for folder, _, files in os.walk(self.root_folder):
            if len(files) > 0:
                for file in files:
                    if 'dbfid' in file:
                        dbfid = int(file.split('dbfid')[1].split('n')[0])
                        if dbfid in dict_files['FileID']:
                            # Duplicate file

                            if warned_once is False:
                                warnings.warn('Duplicate file(s) found. See duplicates property.')

                                warned_once = True
                                self.duplicates = []

                            dup_index = dict_files['FileID'].index(dbfid)
                            dup_file = dict_files['FileName'][dup_index]

                            self.duplicates.append(
                                (folder + '/' + file, dup_file))

                        else:
                            dict_files['FileID'].append(dbfid)
                            dict_files['FileName'].append(
                                folder + '/' + file)

        # Convert to a Pandas DataFrame
        return pd.DataFrame(dict_files)


    def _filter_table(self, table, filters):
        """Apply filters on a DataFrame, return the filtered DataFrame."""
        for column in filters:
            if column in table.columns:
                table = table[table[column] == filters[column]]
        return table

    def get(self, participant='', session='', trial='', file=''):
        """
        Extract information from a project.

        Parameters
        ----------
        participant : str, optional
            Participant label (for example, 'P01'). The default is ''.
        session : str, optional
            Session label (for example, 'SB4320'). The default is ''.
        trial : str, optional
            Trial label (for example, 'StaticAnatomic'). The default is ''.
        file : str, optional
            File label (for example, 'Kinematics'). The default is ''.

        Returns
        -------
        dict
            A record of the specified information.

        """
        # Assign the tables
        if participant == '' and session == '' and trial == '' and file == '':
            table_name = 'Projects'
            contents_name = 'Participants'
            contents_field = 'ProjectLabel'
            contents_filter = self.project_label
        elif participant != '' and session == '' and trial == '' and file == '':
            table_name = 'Participants'
            contents_name = 'Sessions'
            contents_field = 'ParticipantLabel'
            contents_filter = participant
        elif participant != '' and session != '' and trial == '' and file == '':
            table_name = 'Sessions'
            contents_name = 'Trials'
            contents_field = 'SessionLabel'
            contents_filter = session
        elif participant != '' and session != '' and trial != '' and file == '':
            table_name = 'Trials'
            contents_name = 'Files'
            contents_field = 'TrialLabel'
            contents_filter = trial
        elif participant != '' and session != '' and trial != '' and file != '':
            table_name = 'Files'
            contents_name = ''
            contents_field = 'FileLabel'
            contents_filter = file
        else:
            raise ValueError('Bad combination of arguments')

        table = self.tables[table_name]
        if contents_name != '':
            contents = self.tables[contents_name]
        else:
            contents = None

        # Filter
        filters = dict()
        if participant != '':
            filters['ParticipantLabel'] = participant
        if session != '':
            filters['SessionLabel'] = session
        if trial != '':
            filters['TrialLabel'] = trial
        if file != '':
            filters['FileLabel'] = file

        table = self._filter_table(table, filters)
        if contents is not None:
            contents = self._filter_table(contents, filters)

        # Change nans to None
        table = table.where(pd.notnull(table), None)

        # Convert to dict
        dict_out = table.to_dict('record')

        if len(dict_out) < 1:
            raise ValueError('No item found.')
        elif len(dict_out) > 1:
            raise ValueError('More than one item found.')
        else:
            dict_out = dict_out[0]

        # Add the contents
        if contents is not None:
            contents = contents[
                contents[contents_field] == contents_filter]
            contents = contents[contents_name[0:-1] + 'Label']
            dict_out[contents_name] = contents.to_list()

        return dict_out

    def refresh(self):
        """Update from database and reindex files."""
        def repetition_to_str(repetition):
            try:
                repetition = str(int(repetition))
            except Exception:
                repetition = ''
            return repetition

        self.tables = dict()

        self.tables['Projects'] = self._fetch_table('Projects')

        # Participants
        self.tables['Participants'] = self._fetch_table('Participants')
        self.tables['Participants']['ProjectLabel'] = self.project_label

        # Sessions
        self.tables['Sessions'] = self._fetch_table('Sessions')
        self.tables['Sessions'] = self.tables['Sessions'].merge(
            self.tables['Participants'][
                ['ParticipantID', 'ParticipantLabel']], how='left')
        self.tables['Sessions']['SessionLabel'] = (
            self.tables['Sessions']['PlaceLabel'] +
            self.tables['Sessions']['SessionRepetition'].apply(repetition_to_str))

        # Trials
        self.tables['Trials'] = self._fetch_table('Trials')
        self.tables['TrialTypes'] = self._fetch_table('TrialTypes')
        self.tables['Trials'] = self.tables['Trials'].merge(
            self.tables['TrialTypes'], how='left')
        self.tables['Trials'] = self.tables['Trials'].merge(
            self.tables['Sessions'][[
                'SessionID', 'SessionLabel', 'ParticipantLabel']], how='left')
        self.tables['Trials']['TrialLabel'] = (
            self.tables['Trials']['TrialTypeLabel'] +
            self.tables['Trials']['TrialRepetition'].apply(repetition_to_str))

        # Files
        self.tables['Files'] = self._fetch_table('Files')
        self.tables['FileTypes'] = self._fetch_table('FileTypes')
        self.tables['FileAssociations'] = self._scan_files()

        self.tables['Files'] = self.tables['Files'].merge(
            self.tables['FileTypes'], how='left')
        self.tables['Files'] = self.tables['Files'].merge(
            self.tables['FileAssociations'], how='left')
        self.tables['Files'] = self.tables['Files'].merge(
            self.tables['Trials'][[
                'TrialID', 'TrialLabel', 'SessionLabel',
                'ParticipantLabel']], how='left')
        self.tables['Files']['dbfid'] = ('dbfid' +
            self.tables['Files']['FileID'].apply(str) + 'n')
        self.tables['Files']['FileLabel'] = \
            self.tables['Files']['FileTypeLabel']


    def rename(self, filename, dbfid):
        """
        Rename a file to include or modify a dbfid code in its filename.

        Parameters
        ----------
        file : str
            Name of the file to rename
        dbfid : int
            FileID in database

        Returns
        -------
        None.
        """
        base, ext = os.path.splitext(filename)

        if 'dbfid' in base:
            base_left_part, rest = base.split('dbfid')
            old_file_id, base_right_part = rest.split('n')
        else:
            base_left_part = base + '_'
            base_right_part = ''

        new_filename = (base_left_part + 'dbfid' + str(dbfid) + 'n' +
                        base_right_part + ext)

        os.rename(filename, new_filename)


    def add_file_entry(self, trial_id, file_type_label):
        """
        Create a file entry in the database.

        The project's 'Files' table is updated after adding the file entry.

        Parameters
        ----------
        trial_id : int
            Trial identifier in the database. Can be obtained using
            get(participant, session, trial)['TrialID'].
        file_type_label str
            File type label.

        Returns
        -------
        None.
        """
        # Find the file type ID
        file_type_table = self.tables['FileTypes']
        file_type_table = file_type_table[
            file_type_table['FileTypeLabel'] == file_type_label]
        file_type_table = file_type_table['FileTypeID']
        if file_type_table.shape[0] != 1:
            raise ValueError('No or multiple IDs found for this file type id.')
        else:
            file_type_id = file_type_table.iloc[0]

        print(f'Trial {trial_id}, FileTypeID {file_type_id}')
        print(requests.post(self.url + '/kineticstoolkit/dbinterface.php',
                            {'username': self.user,
                             'password': self._password,
                             'action': 'createfileentry',
                             'trialid': trial_id,
                             'filetypeid': file_type_id}).text)

        self.refresh()
        return


    def batch_rename(self, folder, new_file_type_label,
                     create_file_entries=False, dry_run=True):
        """
        Batch-rename a set of files to their new corresponding dbfid.

        This function is helpful to quickly assign new dbfids to a batch
        of processed file that share the same name as their preprocessed
        counterpart, when the preprocessed files already have dbfids.

        As a practical example, let's say we have a folder full of raw
        kinematics take files, and we batch-export those files to a new
        folder of c3d files. Both the raw take files and the c3d files share
        the same name, apart from the extension.

        Now, let say a project contains these filetypes:
            - 'RawKinematics': raw kinematic take files;
            - 'LabelledKinematics': c3d files with labelled markers.

        If the raw kinematics files were correctly assigned to database entries
        before batch-exporting, then the exported c3d files contain the
        original (incorrect) dbfid entry in their file names.

        This function changes the file names of the exported files so that
        they match their correct entry in the database.

        Parameters
        ----------
        folder : str
            Folder that contains the set of files to rename. These files must
            have the original dbfid in their name, to identify the trial they
            belong to.
        new_file_type_label : str
            FileTypeLabel as set in the database. For example:
            'LabelledKinematics'.
        create_file_entries : bool (optional)
            If a file entry for the specified file type ID does not exist in
            the found trial, create the file entry in the database, then
            rename the file accordingly. Default is False.
        dry_run : bool (optional)
            When True, the list of file renames is returned, but no action is
            actually taken. Default is True.

        Returns
        -------
        dict with these keys:
            'Rename' :  list of tuples (old_file_name, new_file_name).
            'Ignore' :  list of files without a dbfid.
            'NoFileTypeLabel' : list of files which associated trial does not
                                contain the specified FileTypeLabel
        """
        out = dict()
        out['Rename'] = []
        out['Ignore'] = []
        out['NoFileTypeLabel'] = []

        # Run through the specified folder
        files = os.listdir(folder)

        for filename in files:
            if not 'dbfid' in filename:
                out['Ignore'].append(filename)
                continue

            # Extract incorrect FileID
            filename_left_part, rest = filename.split('dbfid')
            old_file_id, filename_right_part = rest.split('n')

            old_file_id = int(old_file_id)

            # Find corresponding trial
            trial_id = self.tables['Files']['TrialID'][
                self.tables['Files']['FileID'] == old_file_id].iloc[0]

            # Define correct FileID
            def find_new_file_id():
                # Return the file ID that corresponds to the specified
                # trial id and file type label. This is a function so that
                # it can easily be called twice.
                trial_files = self.tables['Files'][
                    self.tables['Files']['TrialID'] == trial_id]
                trial_files = trial_files['FileID'][
                    trial_files['FileTypeLabel'] == new_file_type_label]

                if trial_files.shape[0] == 1:
                    new_file_id = trial_files.iloc[0]
                else:
                    new_file_id = None
                return new_file_id

            new_file_id = find_new_file_id()

            if new_file_id is None and dry_run is False:
                # No FileID was found for this FileTypeLabel.
                if create_file_entries is True:
                    print(f'Adding file entry for {filename}')
                    self.add_file_entry(trial_id, new_file_type_label)
                    new_file_id = find_new_file_id()

            if new_file_id is None:
                # No FileID was found for this FileTypeLabel, even after
                # creating the file entry. This shouldn't happen unless
                # on dry runs.
                print(f'Found no file entry for {filename}')
                out['NoFileTypeLabel'].append(filename)
                continue

            # Set new file name
            new_file_name = (filename_left_part + 'dbfid' +
                             str(new_file_id) + 'n' +
                             filename_right_part)

            out['Rename'].append((filename, new_file_name))

        if dry_run:
            print('Dry run. No file was renamed.')
        else:
            for element in out['Rename']:
                os.rename(folder + '/' + element[0],
                          folder + '/' + element[1])
            # Refresh the project, so that new-renamed files can be indexed
            # accordingly.
            self.refresh()

        return out
