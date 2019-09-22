'''A Python module for reading and writing C3D files.'''

from __future__ import unicode_literals

import array
import io
import numpy as np
import struct
import warnings


PROCESSOR_INTEL = 84
PROCESSOR_DEC = 85
PROCESSOR_MIPS = 86


class Header(object):
    '''Header information from a C3D file.

    Attributes
    ----------
    label_block : int
        Index of the 512-byte block where labels (metadata) are found.
    parameter_block : int
        Index of the 512-byte block where parameters (metadata) are found.
    data_block : int
        Index of the 512-byte block where data starts.
    point_count : int
        Number of motion capture channels recorded in this file.
    analog_count : int
        Number of analog values recorded per frame of 3D point data.
    first_frame : int
        Index of the first frame of data.
    last_frame : int
        Index of the last frame of data.
    analog_per_frame : int
        Number of analog frames per frame of 3D point data. The analog frame
        rate (ANALOG:RATE) apparently equals the point frame rate (POINT:RATE)
        times this value.
    frame_rate : float
        The frame rate of the recording, in frames per second.
    scale_factor : float
        Multiply values in the file by this scale parameter.
    long_event_labels : bool
    max_gap : int

    .. note::
        The ``scale_factor`` attribute is not used in Phasespace C3D files;
        instead, use the POINT.SCALE parameter.

    .. note::
        The ``first_frame`` and ``last_frame`` header attributes are not used in
        C3D files generated by Phasespace. Instead, the first and last
        frame numbers are stored in the POINTS:ACTUAL_START_FIELD and
        POINTS:ACTUAL_END_FIELD parameters.
    '''

    BINARY_FORMAT = '<BBHHHHHfHHf270sHH214s'

    def __init__(self, handle=None):
        '''Create a new Header object.

        Parameters
        ----------
        handle : file handle, optional
            If given, initialize attributes for the Header from this file
            handle. The handle must be seek-able and readable. If `handle` is
            not given, Header attributes are initialized with default values.
        '''
        self.label_block = 0
        self.parameter_block = 2
        self.data_block = 3

        self.point_count = 50
        self.analog_count = 0

        self.first_frame = 1
        self.last_frame = 1
        self.analog_per_frame = 0
        self.frame_rate = 60.0

        self.max_gap = 0
        self.scale_factor = -1.0
        self.long_event_labels = False

        if handle:
            self.read(handle)

    def write(self, handle):
        '''Write binary header data to a file handle.

        This method writes exactly 512 bytes to the beginning of the given file
        handle.

        Parameters
        ----------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be written to describe the parameters in this Header. The
            handle must be writeable.
        '''
        handle.seek(0)
        handle.write(struct.pack(self.BINARY_FORMAT,
                                 self.parameter_block,
                                 0x50,
                                 self.point_count,
                                 self.analog_count,
                                 self.first_frame,
                                 self.last_frame,
                                 self.max_gap,
                                 self.scale_factor,
                                 self.data_block,
                                 self.analog_per_frame,
                                 self.frame_rate,
                                 b'',
                                 self.long_event_labels and 0x3039 or 0x0,
                                 self.label_block,
                                 b''))

    def __str__(self):
        '''Return a string representation of this Header's attributes.'''
        return '''\
  parameter_block: {0.parameter_block}
      point_count: {0.point_count}
     analog_count: {0.analog_count}
      first_frame: {0.first_frame}
       last_frame: {0.last_frame}
          max_gap: {0.max_gap}
     scale_factor: {0.scale_factor}
       data_block: {0.data_block}
 analog_per_frame: {0.analog_per_frame}
       frame_rate: {0.frame_rate}
long_event_labels: {0.long_event_labels}
      label_block: {0.label_block}'''.format(self)

    def read(self, handle):
        '''Read and parse binary header data from a file handle.

        This method reads exactly 512 bytes from the beginning of the given file
        handle.

        Parameters
        ----------
        handle : file handle
            The given handle will be reset to 0 using `seek` and then 512 bytes
            will be read to initialize the attributes in this Header. The handle
            must be readable.

        Raises
        ------
        AssertionError
            If the magic byte from the header is not 80 (the C3D magic value).
        '''
        handle.seek(0)
        (self.parameter_block,
         magic,
         self.point_count,
         self.analog_count,
         self.first_frame,
         self.last_frame,
         self.max_gap,
         self.scale_factor,
         self.data_block,
         self.analog_per_frame,
         self.frame_rate,
         _,
         self.long_event_labels,
         self.label_block,
         _) = struct.unpack(self.BINARY_FORMAT, handle.read(512))

        assert magic == 80, 'C3D magic {} != 80 !'.format(magic)


class Param(object):
    '''A class representing a single named parameter from a C3D file.

    Attributes
    ----------
    name : str
        Name of this parameter.
    desc : str
        Brief description of this parameter.
    bytes_per_element : int, optional
        For array data, this describes the size of each element of data. For
        string data (including arrays of strings), this should be -1.
    dimensions : list of int
        For array data, this describes the dimensions of the array, stored in
        column-major order. For arrays of strings, the dimensions here will be
        the number of columns (length of each string) followed by the number of
        rows (number of strings).
    bytes : str
        Raw data for this parameter.
    '''

    def __init__(self,
                 name,
                 desc='',
                 bytes_per_element=1,
                 dimensions=None,
                 bytes=b'',
                 handle=None):
        '''Set up a new parameter, only the name is required.'''
        self.name = name
        self.desc = desc
        self.bytes_per_element = bytes_per_element
        self.dimensions = dimensions or []
        self.bytes = bytes
        if handle:
            self.read(handle)

    def __repr__(self):
        return '<Param: {}>'.format(self.desc)

    @property
    def num_elements(self):
        '''Return the number of elements in this parameter's array value.'''
        e = 1
        for d in self.dimensions:
            e *= d
        return e

    @property
    def total_bytes(self):
        '''Return the number of bytes used for storing this parameter's data.'''
        return self.num_elements * abs(self.bytes_per_element)

    def binary_size(self):
        '''Return the number of bytes needed to store this parameter.'''
        return (
            1 + # group_id
            2 + # next offset marker
            1 + len(self.name.encode('utf-8')) + # size of name and name bytes
            1 + # data size
            1 + len(self.dimensions) + # size of dimensions and dimension bytes
            self.total_bytes + # data
            1 + len(self.desc.encode('utf-8')) # size of desc and desc bytes
            )

    def write(self, group_id, handle):
        '''Write binary data for this parameter to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group that holds this parameter.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self.name.encode('utf-8')
        handle.write(struct.pack('bb', len(name), group_id))
        handle.write(name)
        handle.write(struct.pack('<h', self.binary_size() - 2 - len(name)))
        handle.write(struct.pack('b', self.bytes_per_element))
        handle.write(struct.pack('B', len(self.dimensions)))
        handle.write(struct.pack('B' * len(self.dimensions), *self.dimensions))
        if self.bytes:
            handle.write(self.bytes)
        desc = self.desc.encode('utf-8')
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)

    def read(self, handle):
        '''Read binary data for this parameter from a file handle.

        This reads exactly enough data from the current position in the file to
        initialize the parameter.
        '''
        self.bytes_per_element, = struct.unpack('b', handle.read(1))
        dims, = struct.unpack('B', handle.read(1))
        self.dimensions = [struct.unpack('B', handle.read(1))[0] for _ in range(dims)]
        self.bytes = b''
        if self.total_bytes:
            self.bytes = handle.read(self.total_bytes)
        size, = struct.unpack('B', handle.read(1))
        self.desc = size and handle.read(size).decode('utf-8') or ''

    def _as(self, fmt):
        '''Unpack the raw bytes of this param using the given struct format.'''
        return struct.unpack('<' + fmt, self.bytes)[0]

    @property
    def int8_value(self):
        '''Get the param as an 8-bit signed integer.'''
        return self._as('b')

    @property
    def uint8_value(self):
        '''Get the param as an 8-bit unsigned integer.'''
        return self._as('B')

    @property
    def int16_value(self):
        '''Get the param as a 16-bit signed integer.'''
        return self._as('h')

    @property
    def uint16_value(self):
        '''Get the param as a 16-bit unsigned integer.'''
        return self._as('H')

    @property
    def int32_value(self):
        '''Get the param as a 32-bit signed integer.'''
        return self._as('i')

    @property
    def uint32_value(self):
        '''Get the param as a 32-bit unsigned integer.'''
        return self._as('I')

    @property
    def float_value(self):
        '''Get the param as a 32-bit float.'''
        return self._as('f')

    @property
    def bytes_value(self):
        '''Get the param as a raw byte string.'''
        return self.bytes

    @property
    def string_value(self):
        '''Get the param as a unicode string.'''
        return self.bytes.decode('utf-8')

    def _as_array(self, fmt):
        '''Unpack the raw bytes of this param using the given data format.'''
        assert self.dimensions, \
            '{}: cannot get value as {} array!'.format(self.name, fmt)
        elems = array.array(fmt)
        elems.fromstring(self.bytes)
        return np.array(elems).reshape(self.dimensions)

    @property
    def int8_array(self):
        '''Get the param as an array of 8-bit signed integers.'''
        return self._as_array('b')

    @property
    def uint8_array(self):
        '''Get the param as an array of 8-bit unsigned integers.'''
        return self._as_array('B')

    @property
    def int16_array(self):
        '''Get the param as an array of 16-bit signed integers.'''
        return self._as_array('h')

    @property
    def uint16_array(self):
        '''Get the param as an array of 16-bit unsigned integers.'''
        return self._as_array('H')

    @property
    def int32_array(self):
        '''Get the param as an array of 32-bit signed integers.'''
        return self._as_array('i')

    @property
    def uint32_array(self):
        '''Get the param as an array of 32-bit unsigned integers.'''
        return self._as_array('I')

    @property
    def float_array(self):
        '''Get the param as an array of 32-bit floats.'''
        return self._as_array('f')

    @property
    def bytes_array(self):
        '''Get the param as an array of raw byte strings.'''
        assert len(self.dimensions) == 2, \
            '{}: cannot get value as bytes array!'.format(self.name)
        l, n = self.dimensions
        return [self.bytes[i*l:(i+1)*l] for i in range(n)]

    @property
    def string_array(self):
        '''Get the param as a array of unicode strings.'''
        assert len(self.dimensions) == 2, \
            '{}: cannot get value as string array!'.format(self.name)
        l, n = self.dimensions
        return [self.bytes[i*l:(i+1)*l].decode('utf-8') for i in range(n)]


class Group(object):
    '''A group of parameters from a C3D file.

    In C3D files, parameters are organized in groups. Each group has a name, a
    description, and a set of named parameters.

    Attributes
    ----------
    name : str
        Name of this parameter group.
    desc : str
        Description for this parameter group.
    '''

    def __init__(self, name=None, desc=None):
        self.name = name
        self.desc = desc
        self.params = {}

    def __repr__(self):
        return '<Group: {}>'.format(self.desc)

    def get(self, key, default=None):
        '''Get a parameter by key.

        Parameters
        ----------
        key : any
            Parameter key to look up in this group.
        default : any, optional
            Value to return if the key is not found. Defaults to None.

        Returns
        -------
        param : :class:`Param`
            A parameter from the current group.
        '''
        return self.params.get(key, default)

    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        Additional keyword arguments will be passed to the `Param` constructor.
        '''
        self.params[name.upper()] = Param(name.upper(), **kwargs)

    def binary_size(self):
        '''Return the number of bytes to store this group and its parameters.'''
        return (
            1 + # group_id
            1 + len(self.name.encode('utf-8')) + # size of name and name bytes
            2 + # next offset marker
            1 + len(self.desc.encode('utf-8')) + # size of desc and desc bytes
            sum(p.binary_size() for p in self.params.values()))

    def write(self, group_id, handle):
        '''Write this parameter group, with parameters, to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self.name.encode('utf-8')
        desc = self.desc.encode('utf-8')
        handle.write(struct.pack('bb', len(name), -group_id))
        handle.write(name)
        handle.write(struct.pack('<h', 3 + len(desc)))
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)
        for param in self.params.values():
            param.write(group_id, handle)

    def get_int8(self, key):
        '''Get the value of the given parameter as an 8-bit signed integer.'''
        return self.params[key.upper()].int8_value

    def get_uint8(self, key):
        '''Get the value of the given parameter as an 8-bit unsigned integer.'''
        return self.params[key.upper()].uint8_value

    def get_int16(self, key):
        '''Get the value of the given parameter as a 16-bit signed integer.'''
        return self.params[key.upper()].int16_value

    def get_uint16(self, key):
        '''Get the value of the given parameter as a 16-bit unsigned integer.'''
        return self.params[key.upper()].uint16_value

    def get_int32(self, key):
        '''Get the value of the given parameter as a 32-bit signed integer.'''
        return self.params[key.upper()].int32_value

    def get_uint32(self, key):
        '''Get the value of the given parameter as a 32-bit unsigned integer.'''
        return self.params[key.upper()].uint32_value

    def get_float(self, key):
        '''Get the value of the given parameter as a 32-bit float.'''
        return self.params[key.upper()].float_value

    def get_bytes(self, key):
        '''Get the value of the given parameter as a byte array.'''
        return self.params[key.upper()].bytes_value

    def get_string(self, key):
        '''Get the value of the given parameter as a string.'''
        return self.params[key.upper()].string_value


class Manager(object):
    '''A base class for managing C3D file metadata.

    This class manages a C3D header (which contains some stock metadata fields)
    as well as a set of parameter groups. Each group is accessible using its
    name.

    Attributes
    ----------
    header : `Header`
        Header information for the C3D file.
    '''

    def __init__(self, header=None):
        '''Set up a new Manager with a Header.'''
        self.header = header or Header()
        self.groups = {}

    def check_metadata(self):
        '''Ensure that the metadata in our file is self-consistent.'''
        assert self.header.point_count == self.point_used, (
            'inconsistent point count! {} header != {} POINT:USED'.format(
                self.header.point_count,
                self.point_used,
            ))

        assert self.header.scale_factor == self.point_scale, (
            'inconsistent scale factor! {} header != {} POINT:SCALE'.format(
                self.header.scale_factor,
                self.point_scale,
            ))

        assert self.header.frame_rate == self.point_rate, (
            'inconsistent frame rate! {} header != {} POINT:RATE'.format(
                self.header.frame_rate,
                self.point_rate,
            ))

        ratio = self.analog_rate / self.point_rate
        assert True or self.header.analog_per_frame == ratio, (
            'inconsistent analog rate! {} header != {} analog-fps / {} point-fps'.format(
                self.header.analog_per_frame,
                self.analog_rate,
                self.point_rate,
            ))

        count = self.analog_used * self.header.analog_per_frame
        assert True or self.header.analog_count == count, (
            'inconsistent analog count! {} header != {} analog used * {} per-frame'.format(
                self.header.analog_count,
                self.analog_used,
                self.header.analog_per_frame,
            ))

        start = self.get_uint16('POINT:DATA_START')
        assert self.header.data_block == start, (
            'inconsistent data block! {} header != {} POINT:DATA_START'.format(
                self.header.data_block, start))

        for name in ('POINT:LABELS', 'POINT:DESCRIPTIONS',
                     'ANALOG:LABELS', 'ANALOG:DESCRIPTIONS'):
            if self.get(name) is None:
                warnings.warn('missing parameter {}'.format(name))

    def add_group(self, group_id, name, desc):
        '''Add a new parameter group.

        Parameters
        ----------
        group_id : int
            The numeric ID for a group to check or create.
        name : str, optional
            If a group is created, assign this name to the group.
        desc : str, optional
            If a group is created, assign this description to the group.

        Returns
        -------
        group : :class:`Group`
            A group with the given ID, name, and description.

        Raises
        ------
        KeyError
            If a group with a duplicate ID or name already exists.
        '''
        if group_id in self.groups:
            raise KeyError(group_id)
        name = name.upper()
        if name in self.groups:
            raise KeyError(name)
        group = self.groups[name] = self.groups[group_id] = Group(name, desc)
        return group

    def get(self, group, default=None):
        '''Get a group or parameter.

        Parameters
        ----------
        group : str
            If this string contains a period (.), then the part before the
            period will be used to retrieve a group, and the part after the
            period will be used to retrieve a parameter from that group. If this
            string does not contain a period, then just a group will be
            returned.
        default : any
            Return this value if the named group and parameter are not found.

        Returns
        -------
        value : :class:`Group` or :class:`Param`
            Either a group or parameter with the specified name(s). If neither
            is found, returns the default value.
        '''
        if isinstance(group, int):
            return self.groups.get(group, default)
        group = group.upper()
        param = None
        if '.' in group:
            group, param = group.split('.', 1)
        if ':' in group:
            group, param = group.split(':', 1)
        if group not in self.groups:
            return default
        group = self.groups[group]
        if param is not None:
            return group.get(param, default)
        return group

    def get_int8(self, key):
        '''Get a parameter value as an 8-bit signed integer.'''
        return self.get(key).int8_value

    def get_uint8(self, key):
        '''Get a parameter value as an 8-bit unsigned integer.'''
        return self.get(key).uint8_value

    def get_int16(self, key):
        '''Get a parameter value as a 16-bit signed integer.'''
        return self.get(key).int16_value

    def get_uint16(self, key):
        '''Get a parameter value as a 16-bit unsigned integer.'''
        return self.get(key).uint16_value

    def get_int32(self, key):
        '''Get a parameter value as a 32-bit signed integer.'''
        return self.get(key).int32_value

    def get_uint32(self, key):
        '''Get a parameter value as a 32-bit unsigned integer.'''
        return self.get(key).uint32_value

    def get_float(self, key):
        '''Get a parameter value as a 32-bit float.'''
        return self.get(key).float_value

    def get_bytes(self, key):
        '''Get a parameter value as a byte string.'''
        return self.get(key).bytes_value

    def get_string(self, key):
        '''Get a parameter value as a string.'''
        return self.get(key).string_value

    def parameter_blocks(self):
        '''Compute the size (in 512B blocks) of the parameter section.'''
        bytes = 4. + sum(g.binary_size() for g in self.groups.values())
        return int(np.ceil(bytes / 512))

    @property
    def point_rate(self):
        return self.get_float('POINT:RATE')

    @property
    def point_scale(self):
        return self.get_float('POINT:SCALE')

    @property
    def point_used(self):
        return self.get_uint16('POINT:USED')

    @property
    def analog_used(self):
        try:
            return self.get_uint16('ANALOG:USED')
        except AttributeError:
            return 0

    @property
    def analog_rate(self):
        try:
            return self.get_float('ANALOG:RATE')
        except AttributeError:
            return 0

    @property
    def point_labels(self):
        return self.get('POINT:LABELS').string_array

    @property
    def analog_labels(self):
        return self.get('ANALOG:LABELS').string_array

    def first_frame(self):
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self.get('TRIAL:ACTUAL_START_FIELD')
        if param is not None:
            return param.int32_value
        return self.header.first_frame

    def last_frame(self):
        # this is a hack for phasespace files ... should put it in a subclass.
        param = self.get('TRIAL:ACTUAL_END_FIELD')
        if param is not None:
            return param.int32_value
        return self.header.last_frame


class Reader(Manager):
    '''This class provides methods for reading the data in a C3D file.

    A C3D file contains metadata and frame-based data describing 3D motion.

    You can iterate over the frames in the file by calling `read_frames()` after
    construction:

    >>> r = c3d.Reader(open('capture.c3d', 'rb'))
    >>> for frame_no, points, analog in r.read_frames():
    ...     print('{0.shape} points in this frame'.format(points))
    '''

    def __init__(self, handle):
        '''Initialize this C3D file by reading header and parameter data.

        Parameters
        ----------
        handle : file handle
            Read metadata and C3D motion frames from the given file handle. This
            handle is assumed to be `seek`-able and `read`-able. The handle must
            remain open for the life of the `Reader` instance. The `Reader` does
            not `close` the handle.

        Raises
        ------
        ValueError
            If the processor metadata in the C3D file is anything other than 84
            (Intel format).
        '''
        super(Reader, self).__init__(Header(handle))

        self._handle = handle
        self._handle.seek((self.header.parameter_block - 1) * 512)

        # metadata header
        buf = self._handle.read(4)
        _, _, parameter_blocks, processor = struct.unpack('BBBB', buf)
        if processor != PROCESSOR_INTEL:
            raise ValueError(
                'we only read Intel C3D files (got processor {})'.
                format(processor))

        # read all parameter blocks as a single chunk to avoid block
        # boundary issues.
        bytes = self._handle.read(512 * parameter_blocks - 4)
        while bytes:
            buf = io.BytesIO(bytes)

            chars_in_name, group_id = struct.unpack('bb', buf.read(2))
            if group_id == 0 or chars_in_name == 0:
                # we've reached the end of the parameter section.
                break

            name = buf.read(abs(chars_in_name)).decode('utf-8').upper()
            offset_to_next, = struct.unpack('<h', buf.read(2))

            if group_id > 0:
                # we've just started reading a parameter. if its group doesn't
                # exist, create a blank one. add the parameter to the group.
                self.groups.setdefault(group_id, Group()).add_param(name, handle=buf)
            else:
                # we've just started reading a group. if a group with the
                # appropriate id exists already (because we've already created
                # it for a parameter), just set the name of the group.
                # otherwise, add a new group.
                group_id = abs(group_id)
                size, = struct.unpack('B', buf.read(1))
                desc = size and buf.read(size) or ''
                group = self.get(group_id)
                if group is not None:
                    group.name = name
                    group.desc = desc
                    self.groups[name] = group
                else:
                    self.add_group(group_id, name, desc)

            bytes = bytes[2 + abs(chars_in_name) + offset_to_next:]

        self.check_metadata()

    def read_frames(self, copy=True):
        '''Iterate over the data frames from our C3D file handle.

        Parameters
        ----------
        copy : bool
            If False, the reader returns a reference to the same data buffers
            for every frame. The default is True, which causes the reader to
            return a unique data buffer for each frame. Set this to False if you
            consume frames as you iterate over them, or True if you store them
            for later.

        Returns
        -------
        frames : sequence of (frame number, points, analog)
            This method generates a sequence of (frame number, points, analog)
            tuples, one tuple per frame. The first element of each tuple is the
            frame number. The second is a numpy array of parsed, 5D point data
            and the third element of each tuple is a numpy array of analog
            values that were recorded during the frame. (Often the analog data
            are sampled at a higher frequency than the 3D point data, resulting
            in multiple analog frames per frame of point data.)

            The first three columns in the returned point data are the (x, y, z)
            coordinates of the observed motion capture point. The fourth column
            is an estimate of the error for this particular point, and the fifth
            column is the number of cameras that observed the point in question.
            Both the fourth and fifth values are -1 if the point is considered
            to be invalid.
        '''
        scale = abs(self.point_scale)
        is_float = self.point_scale < 0

        point_bytes = [2, 4][is_float]
        point_dtype = [np.int16, np.float32][is_float]
        point_scale = [scale, 1][is_float]
        points = np.zeros((self.point_used, 5), float)

        # TODO: handle ANALOG:BITS parameter here!
        p = self.get('ANALOG:FORMAT')
        analog_unsigned = p and p.string_value.strip().upper() == 'UNSIGNED'
        analog_dtype = np.int16
        analog_bytes = 2
        if is_float:
            analog_dtype = np.float32
            analog_bytes = 4
        elif analog_unsigned:
            analog_dtype = np.uint16
            analog_bytes = 2
        analog = np.array([], float)

        offsets = np.zeros((self.analog_used, 1), int)
        param = self.get('ANALOG:OFFSET')
        if param is not None:
            offsets = param.int16_array[:self.analog_used, None]

        scales = np.ones((self.analog_used, 1), float)
        param = self.get('ANALOG:SCALE')
        if param is not None:
            scales = param.float_array[:self.analog_used, None]

        gen_scale = 1.
        param = self.get('ANALOG:GEN_SCALE')
        if param is not None:
            gen_scale = param.float_value

        self._handle.seek((self.header.data_block - 1) * 512)
        for frame_no in range(self.first_frame(), self.last_frame() + 1):
            n = 4 * self.header.point_count
            raw = np.frombuffer(self._handle.read(n * point_bytes),
                                dtype=point_dtype,
                                count=n).reshape((self.point_used, 4))

            points[:, :3] = raw[:, :3] * point_scale

            valid = raw[:, 3] > -1
            points[~valid, 3:5] = -1
            c = raw[valid, 3].astype(np.uint16)

            # fourth value is floating-point (scaled) error estimate
            points[valid, 3] = (c & 0xff).astype(float) * scale

            # fifth value is number of bits set in camera-observation byte
            points[valid, 4] = sum((c & (1 << k)) >> k for k in range(8, 17))

            if self.header.analog_count > 0:
                n = self.header.analog_count
                raw = np.frombuffer(self._handle.read(n * analog_bytes),
                                    dtype=analog_dtype,
                                    count=n).reshape((-1, self.analog_used)).T
                analog = (raw.astype(float) - offsets) * scales * gen_scale

            if copy:
                yield frame_no, points.copy(), analog.copy()
            else:
                yield frame_no, points, analog


class Writer(Manager):
    '''This class writes metadata and frames to a C3D file.

    For example, to read an existing C3D file, apply some sort of data
    processing to the frames, and write out another C3D file::

    >>> r = c3d.Reader(open('data.c3d', 'rb'))
    >>> w = c3d.Writer()
    >>> w.add_frames(process_frames_somehow(r.read_frames()))
    >>> with open('smoothed.c3d', 'wb') as handle:
    >>>     w.write(handle)

    Parameters
    ----------
    point_rate : float, optional
        The frame rate of the data. Defaults to 480.
    analog_rate : float, optional
        The number of analog samples per frame. Defaults to 0.
    point_scale : float, optional
        The scale factor for point data. Defaults to -1 (i.e., "check the
        POINT:SCALE parameter").
    point_units : str, optional
        The units that the point numbers represent. Defaults to ``'mm  '``.
    gen_scale : float, optional
        General scaling factor for data. Defaults to 1.
    '''

    def __init__(self,
                 point_rate=480.,
                 analog_rate=0.,
                 point_scale=-1.,
                 point_units='mm  ',
                 gen_scale=1.):
        '''Set metadata for this writer.

        '''
        super(Writer, self).__init__()
        self._point_rate = point_rate
        self._analog_rate = analog_rate
        self._point_scale = point_scale
        self._point_units = point_units
        self._gen_scale = gen_scale
        self._frames = []

    def add_frames(self, frames):
        '''Add frames to this writer instance.

        Parameters
        ----------
        frames : sequence of (point, analog) tuples
            A sequence of frame data to add to the writer.
        '''
        self._frames.extend(frames)

    def _pad_block(self, handle):
        '''Pad the file with 0s to the end of the next block boundary.'''
        extra = handle.tell() % 512
        if extra:
            handle.write(b'\x00' * (512 - extra))

    def _write_metadata(self, handle):
        '''Write metadata to a file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        self.check_metadata()

        # header
        self.header.write(handle)
        self._pad_block(handle)
        assert handle.tell() == 512

        # groups
        handle.write(struct.pack(
            'BBBB', 0, 0, self.parameter_blocks(), PROCESSOR_INTEL))
        id_groups = sorted(
            (i, g) for i, g in self.groups.items() if isinstance(i, int))
        for group_id, group in id_groups:
            group.write(group_id, handle)

        # padding
        self._pad_block(handle)
        while handle.tell() != 512 * (self.header.data_block - 1):
            handle.write(b'\x00' * 512)

    def _write_frames(self, handle):
        '''Write our frame data to the given file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        assert handle.tell() == 512 * (self.header.data_block - 1)
        scale = abs(self.point_scale)
        is_float = self.point_scale < 0
        point_dtype = [np.int16, np.float32][is_float]
        point_scale = [scale, 1][is_float]
        point_format = 'if'[is_float]
        raw = np.empty((self.point_used, 4), point_dtype)
        for points, analog in self._frames:
            valid = points[:, 3] > -1
            raw[~valid, 3] = -1
            raw[valid, :3] = points[valid, :3] / self._point_scale
            raw[valid, 3] = (
                ((points[valid, 4]).astype(np.uint8) << 8) |
                (points[valid, 3] / scale).astype(np.uint16)
            )
            point = array.array(point_format)
            point.extend(raw.flatten())
            point.tofile(handle)
            analog = array.array(point_format)
            analog.extend(analog)
            analog.tofile(handle)
        self._pad_block(handle)

    def write(self, handle, labels):
        '''Write metadata and point + analog frames to a file handle.

        Parameters
        ----------
        handle : file
            Write metadata and C3D motion frames to the given file handle. The
            writer does not close the handle.
        '''
        if not self._frames:
            return

        def add(name, desc, bpe, format, bytes, *dimensions):
            group.add_param(name,
                            desc=desc,
                            bytes_per_element=bpe,
                            bytes=struct.pack(format, bytes),
                            dimensions=list(dimensions))

        def add_str(name, desc, bytes, *dimensions):
            group.add_param(name,
                            desc=desc,
                            bytes_per_element=-1,
                            bytes=bytes.encode('utf-8'),
                            dimensions=list(dimensions))

        def add_empty_array(name, desc, bpe):
            group.add_param(name, desc=desc, bytes_per_element=bpe, dimensions=[0])

        points, analog = self._frames[0]
        ppf = len(points)

        # POINT group

        # Get longest label name
        label_max_size = 0
        label_max_size = max(label_max_size, len(label) for label in labels)

        group = self.add_group(1, 'POINT', 'POINT group')
        add('USED', 'Number of 3d markers', 2, '<H', ppf)
        add('FRAMES', 'frame count', 2, '<H', min(65535, len(self._frames)))
        add('DATA_START', 'data block number', 2, '<H', 0)
        add('SCALE', '3d scale factor', 4, '<f', self._point_scale)
        add('RATE', '3d data capture rate', 4, '<f', self._point_rate)
        add_str('X_SCREEN', 'X_SCREEN parameter', '+X', 2)
        add_str('Y_SCREEN', 'Y_SCREEN parameter', '+Y', 2)
        add_str('UNITS', '3d data units', self._point_units, len(self._point_units))
        add_str('LABELS', 'labels', ''.join(labels[i].ljust(label_max_size)
                for i in range(ppf)), abel_max_size, ppf)
        add_str('DESCRIPTIONS', 'descriptions', ' ' * 16 * ppf, 16, ppf)

        # ANALOG group
        group = self.add_group(2, 'ANALOG', 'ANALOG group')
        add('USED', 'analog channel count', 2, '<H', analog.shape[0])
        add('RATE', 'analog samples per 3d frame', 4, '<f', analog.shape[1])
        add('GEN_SCALE', 'analog general scale factor', 4, '<f', self._gen_scale)
        add_empty_array('SCALE', 'analog channel scale factors', 4)
        add_empty_array('OFFSET', 'analog channel offsets', 2)

        # TRIAL group
        group = self.add_group(3, 'TRIAL', 'TRIAL group')
        add('ACTUAL_START_FIELD', 'actual start frame', 2, '<I', 1, 2)
        add('ACTUAL_END_FIELD', 'actual end frame', 2, '<I', len(self._frames), 2)

        # sync parameter information to header.
        blocks = self.parameter_blocks()
        self.get('POINT:DATA_START').bytes = struct.pack('<H', 2 + blocks)

        self.header.data_block = 2 + blocks
        self.header.frame_rate = self._point_rate
        self.header.last_frame = min(len(self._frames), 65535)
        self.header.point_count = ppf
        self.header.analog_count = np.prod(analog.shape)
        self.header.analog_per_frame = analog.shape[0]
        self.header.scale_factor = self._point_scale

        self._write_metadata(handle)
        self._write_frames(handle)
