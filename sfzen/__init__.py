# pylint: disable = too-many-lines
#  sfzen/__init__.py
#
#  Copyright 2024-2026 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
Simple object-oriented SFZ parsing and manipulation.
"""
import logging
from os import linesep
from os.path import relpath
from re import compile as rcompile
from pathlib import Path, PureWindowsPath, PurePosixPath
from math import ceil
try:
	from functools import cache
except ImportError:
	from functools import lru_cache as cache
from functools import cached_property, reduce
from operator import and_, or_
from collections import defaultdict
from shutil import rmtree, move, copy2 as copyfile
from midi_notes import Note, NoteValueError
from sfzen.opcodes import OPCODES
from sfzen.parser import (
	Parser,
	CommentMatch,
	HeaderMatch,
	DefineMatch,
	IncludeMatch,
	OpcodeMatch,
	ParseError
)


# ---------------------------
# "Magic" members:

__all__ = [	'LOG_FORMAT',
			'Element', 'Control', 'Curve', 'Define', 'Effect', 'Global', 'Group', 'Header',
			'Include', 'Master', 'Midi', 'Opcode', 'Region', 'Sample', 'Comment', 'SFZ',
			'ValidationError', 'DataTypeError', 'MinError', 'MaxError',
			'ChoiceError', 'NotFoundError', 'InvalidHeaderError',
			'SAMPLES_ABSPATH', 'SAMPLES_COPY', 'SAMPLES_HARDLINK',
			'SAMPLES_RELPATH', 'SAMPLES_SYMLINK',
			'clone_region',
			'modulates', 'aliases', 'normal_opcode', 'opcode_definition', 'value_definition',
			'midi_note_sort_key', 'sorted_opcode_names', 'sorted_opcodes', 'sorted_opstrings',
			'pitch_range_str', 'velocity_range_str', 'range_description',
			'opcodes_to_opstrings', 'opcode_dict', 'opcodes_to_dict', 'opstrings_to_dict']

__version__ = "2.1.3"


# ---------------------------
# Constants:

LOG_FORMAT = '[%(filename)24s:%(lineno)3d] %(message)s'

# Sample modes used when "save_as" is called
SAMPLES_UNCHANGED		= 0b000
SAMPLES_ABSPATH			= 0b001
SAMPLES_RELPATH			= 0b010
SAMPLES_COPY			= 0b100
SAMPLES_SYMLINK			= 0b110
SAMPLES_HARDLINK		= 0b111

# Mask which flags that samples are to be saved to a different location
SAMPLE_TARGET_CHANGES	= 0b100


# Opcode definition keys
K_CATEGORY		= 'category'
K_NAME			= 'name'
K_ID			= 'id'
K_VERSION		= 'version'
K_DESCRIPTION	= 'description'
K_MODULATES		= 'modulates'
K_MOD_TYPE		= 'mod_type'
K_ALIASES		= 'aliases'
K_INDEXED		= 'indexed'
K_VALUE			= 'value'
K_VAR_TYPE		= 'var_type'
K_UNIT			= 'unit'
K_DEFAULT		= 'default'
K_MIN			= 'min'
K_MAX			= 'max'
K_CHOICES		= 'choices'


# Opcode categories

KEY_DEFINING_OPCODES = [
	'key',
	'lokey',
	'hikey',
	'pitch_keycenter'
]

KEY_TYPE_OPCODES = [
	'key',
	'lokey',
	'hikey',
	'sw_lokey',
	'sw_hikey',
	'sw_last',
	'sw_down',
	'sw_up',
	'sw_previous',
	'sw_default',
	'sw_lolast',
	'sw_hilast',
	'amp_keycenter',
	'xfin_lokey',
	'xfin_hikey',
	'xfout_lokey',
	'xfout_hikey',
	'pan_keycenter',
	'fil_keycenter',
	'pitch_keycenter'
]

LOOP_DEFINITION_OPCODES = [
	'egN_loop',
	'egN_loop_count',
	'loop_count',
	'loop_crossfade',
	'loop_end',
	'loop_length_onccN',
	'loop_lengthccN',
	'loop_mode',
	'loop_start',
	'loop_start_onccN',
	'loop_startccN',
	'loop_tune',
	'loop_type',
	'loopcount',
	'loopend',
	'loopmode',
	'loopstart',
	'looptune',
	'looptype'
]


# Dicts used for compiling ranges

KEY_RANGE_DICT = {
	'lokey'				: 0,
	'hikey'				: 127
}

VEL_RANGE_DICT = {
	'lovel'				: 0,
	'hivel'				: 127
}


# Preferred sort order (render most significant opcodes first)

OPCODE_SORT_ORDER = [
	'lokey',
	'hikey',
	'key',
	'lovel',
	'hivel',
	'lochan',
	'hichan',
	'sample',
	'pitch_keycenter',
	'loop_mode',
	'loop_start',
	'loop_end',
	'offset',
	'group',
	'off_by',
	'ampeg_attack',
	'ampeg_decay',
	'ampeg_delay',
	'ampeg_hold',
	'ampeg_release',
	'ampeg_sustain',
	'amplfo_delay',
	'amplfo_depth',
	'amplfo_freq',
	'volume',
	'pan',
	'cutoff',
	'resonance',
	'transpose',
	'tune',
	'pitch_keytrack',
	'pitch_veltrack',
	'fileg_delay',
	'fileg_attack',
	'fileg_decay',
	'fileg_depth',
	'fileg_sustain',
	'fileg_release',
	'fileg_hold',
	'fil_type',
	'fil_veltrack',
	'fillfo_delay',
	'fillfo_depth',
	'fillfo_freq',
	'effect1',
	'effect2',
	'pitcheg_delay',
	'pitcheg_attack',
	'pitcheg_decay',
	'pitcheg_depth',
	'pitcheg_sustain',
	'pitcheg_release',
	'pitcheg_hold',
	'pitchlfo_delay',
	'pitchlfo_depth',
	'pitchlfo_freq'
]

OPCODE_SORT_LAST = len(OPCODE_SORT_ORDER)
HEADER_SORT_LAST = OPCODE_SORT_LAST + 1


# Regular expressions:

DEFINE_REPLACEMENT_REGEX = rcompile(r'\$(\w+)')
NORML_VELCURVE_REGEX = rcompile(r'amp_velcurve_(\d+)')
NORML_EQNUM_REGEX = rcompile(r'eq\d+_')
NORML_CC_SEARCH_REGEX = rcompile(r'cc\d')
CCX_REPLACEMENT_REGEXES = [
	(rcompile(r'_oncc(\d+)'), '_onccX'),
	(rcompile(r'_cc(\d+)'), '_ccX'),
	(rcompile(r'cc(\d+)'), 'ccX')
]
CCN_REPLACEMENT_REGEXES = [
	(rcompile(r'_oncc(\d+)'), '_onccN'),
	(rcompile(r'_cc(\d+)'), '_ccN'),
	(rcompile(r'cc(\d+)'), 'ccN')
]
PATH_SPLITTER_REGEX = rcompile(r'[\\\/]')
INT_VALIDATOR_REGEX = rcompile(r'-?[0-9]+$')


# ---------------------------
# Functions

def clone_region(region):
	"""
	Make a clone of a region including all of its inherited opcodes.
	"""
	clone = Region()
	for opcode in region.inherited_opcodes().values():
		clone.append(opcode.clone())
	return clone

def key_group_regions(regions):
	"""
	Enclose the regions from the given list of regions sharing the same key range
	in groups, defining the key range in the group and removing the key range
	definition opcodes from the contained regions.

	Returns a list of Group headers.

	If none of the given regions share the same key range, this function will still
	return a list of Group headers, each containing one Region.
	"""
	key_grouped_regions = defaultdict(list)
	for region in regions:
		key_grouped_regions[midi_note_sort_key(region)].append(region)
	groups = []
	for region_list in key_grouped_regions.values():
		group = Group()
		if len(region_list) > 1:
			common_opstrings = group.common_opstrings()
			if any(len(region.opcodes()) > len(common_opstrings) for region in region_list):
				for opcode_name, opcode_value in opstrings_to_dict(common_opstrings).items():
					group.append(Opcode(opcode_name, opcode_value))
					for region in region_list:
						region.remove_opcode(opcode_name)
		for region in sorted(region_list, key = velocity_sort_key):
			if len(region._opcodes):
				group.append(region)
		if len(group.opstrings_used()):
			groups.append(group)
	return groups

def replace_defs(value, define_dict):
	"""
	Replaces all defined variables with the values which they have been defined as.
	"define_dict" is a dict of previously defined values to replace.
	"""
	if define_dict is None or not isinstance(value, str):
		return value
	try:
		return DEFINE_REPLACEMENT_REGEX.sub(lambda m: define_dict[m.group(1)], value)
	except KeyError:
		return value

def os_any_path(value):
	w = PureWindowsPath(value)
	p = PurePosixPath(value)
	return Path(w if len(w.parts) > len(p.parts) else p)

@cache
def normal_opcode(opcode_name, follow_aliases = True):	# pylint: disable = too-many-return-statements
	"""
	Normalizes a "_ccN" opcode opcode_name.
	If "follow_aliases" is True, returns the name of the opcode that this opcode aliases.
	"""
	if opcode_name is None:
		raise RuntimeError('opcode_name is None')
	if opcode_name in OPCODES:
		return aliases(opcode_name) if follow_aliases else opcode_name
	if NORML_VELCURVE_REGEX.match(opcode_name):
		return 'amp_velcurve_N'
	if NORML_EQNUM_REGEX.search(opcode_name):
		opcode_name = NORML_EQNUM_REGEX.sub('eqN_', opcode_name)
		if opcode_name in OPCODES:
			return aliases(opcode_name) if follow_aliases else opcode_name
		if NORML_CC_SEARCH_REGEX.search(opcode_name):
			for regex, repl in CCX_REPLACEMENT_REGEXES:
				sub = regex.sub(repl, opcode_name)
				if sub != opcode_name and sub in OPCODES:
					return aliases(sub) if follow_aliases else opcode_name
	if NORML_CC_SEARCH_REGEX.search(opcode_name):
		for regex, repl in CCN_REPLACEMENT_REGEXES:
			sub = regex.sub(repl, opcode_name)
			if sub != opcode_name:
				# Recurse for opcodes like "eq3_gain_oncc12"
				if sub in OPCODES:
					return aliases(sub) if follow_aliases else opcode_name
				return normal_opcode(sub, follow_aliases)
	return None

@cache
def aliases(opcode_name, only_alias = False):
	"""
	Returns the name of the opcode which the given opcode_name aliases.

	If it is not aliasing another opcode, the return value depends upon the
	"only_alias" argument. When "only_alias" is True, and the given opcode_name
	does not alias another opcode, returns None. When "only_alias" is False (the
	default), and the given opcode_name does not alias another opcode, returns the
	given opcode_name.

	Raises KeyError
	"""
	definition = OPCODES[opcode_name]
	return definition[K_ALIASES] if definition[K_ALIASES] \
		else None if only_alias else opcode_name

@cache
def modulates(opcode_name):
	"""
	Returns the name of the opcode that the given opcode modulates, if applicable.
	"""
	definition = opcode_definition(opcode_name)
	return None if definition is None else definition.get(K_MODULATES)

@cache
def opcode_definition(opcode_name):
	"""
	Normalizes an opcode_name and returns the matching opcode definition.
	"""
	opcode_name = normal_opcode(opcode_name)
	return None if opcode_name is None else OPCODES[opcode_name]

@cache
def value_definition(opcode_name):
	"""
	Normalizes an opcode_name and returns the value definition dict.
	"""
	definition = opcode_definition(opcode_name)
	if definition and K_VALUE in definition:
		if definition[K_MODULATES] and value_is_undefined(definition[K_VALUE]):
			return value_definition(definition[K_MODULATES])
		return definition[K_VALUE]
	return None

def value_is_undefined(value_def):
	"""
	Returns True if the "value" definition from OPCODES defines no type or limits.
	"""
	return all([
		value_def[K_VAR_TYPE] is None,
		value_def[K_UNIT] is None,
		value_def[K_DEFAULT] is None,
		value_def[K_MIN] is None,
		value_def[K_MAX] is None,
		value_def[K_CHOICES] == []
	])

@cache
def type_str(opcode_name):
	"""
	Normalizes an opcode_name and returns the data type.
	"""
	value_def = value_definition(opcode_name)
	return None if value_def is None else value_def[K_VAR_TYPE]

@cache
def unit(opcode_name):
	"""
	Normalizes an opcode_name and returns the type of unit.
	"""
	value_def = value_definition(opcode_name)
	return None if value_def is None else value_def[K_UNIT]

def _list(coll):
	"""
	Convert any basic collection type into a list.
	"""
	if isinstance(coll, list):
		return coll
	if isinstance(coll, dict):
		return list(coll.values())
	return list(coll)

def opcodes_to_opstrings(opcodes):
	"""
	Returns a set of all the string representation (including name and value) of
	all the opcodes given.

	"opcodes" may be any iterable which returns an Opcode on iteration.
	"""
	return set(str(opcode) for opcode in opcodes)

def opcode_dict(coll):
	"""
	Returns a dict {opcode_name:opcode_value} from any basic collection type.

	Elements of the collection may be opstrings or Opcode objects.
	"""
	if len(coll) == 0:
		return []
	coll = _list(coll)
	return opcodes_to_dict(coll) if isinstance(coll[0], Opcode) else opstrings_to_dict(coll)

def opcodes_to_dict(opcode_list: list):
	"""
	Converts a list of Opcode objects into a dict.

	Returns a dict {opcode_name:opcode_value}.
	"""
	return { opcode.name:opcode.value for opcode in opcode_list }

def opstrings_to_dict(opstring_list: list):
	"""
	Converts a list of string representation (including name and value) into a dict.

	Returns a dict {opcode_name:opcode_value}.
	"""
	def _split(s):
		t = s.split('=', 1)
		if len(t) == 2:
			return t
		raise ValueError(f'Could not split opstring: "{s}"')
	return dict(_split(opstring) for opstring in opstring_list )

def _range_str(rng_dict, opdict):
	d = rng_dict.copy()
	d.update(opdict)
	l = list(d.values())
	return f'{l[0]}-{l[1]}'

def pitch_range_str(opcodes):
	"""
	Returns a string like "<lokey>-<hikey>", using pitch numbers (not note names).
	"""
	if opcodes:
		opdict = opcode_dict(opcodes)
		return str(opdict['key']) if 'key' in opdict else _range_str(KEY_RANGE_DICT, opdict)
	return '0-127'

def velocity_range_str(opcodes):
	"""
	Returns a string like "<lovel>-<hivel>".
	"""
	if opcodes:
		opdict = opcode_dict(opcodes)
		return _range_str(VEL_RANGE_DICT, opdict)
	return '0-127'

def range_description(opcodes):
	"""
	Returns a string like "<lokey>-<hikey>, <lovel>-<hivel>".
	Keys are represented using MIDI pitch numbers, not note names.
	"""
	return f' {pitch_range_str(opcodes)}, {velocity_range_str(opcodes)}'

def sorted_elements(elements):
	"""
	Sort a list of elements according to the preferred OPCODE_SORT_ORDER, with
	headers last.
	"""
	def sort_func(element):
		if isinstance(element, Opcode):
			if element.name in OPCODE_SORT_ORDER:
				return OPCODE_SORT_ORDER.index(element.name)
			return OPCODE_SORT_LAST
		return HEADER_SORT_LAST
	return sorted(elements, key = sort_func)

def sorted_opcodes(opcodes):
	"""
	Sort a list of Opcode objects according to the preferred OPCODE_SORT_ORDER.
	"""
	return sorted(opcodes, key = lambda opcode: \
		OPCODE_SORT_ORDER.index(opcode.name) \
		if opcode.name in OPCODE_SORT_ORDER \
		else OPCODE_SORT_LAST)

def sorted_opcode_names(opcodes):
	"""
	Sort a list of strings (opcode names), according to the preferred OPCODE_SORT_ORDER.
	"""
	return sorted(opcodes, key = lambda opcode_name: \
		OPCODE_SORT_ORDER.index(opcode_name) \
		if opcode_name in OPCODE_SORT_ORDER \
		else OPCODE_SORT_LAST)

def sorted_opstrings(opstrings):
	"""
	Sort a list of string representation (including name and value) of opcodes
	according to the preferred OPCODE_SORT_ORDER.
	"""
	def sort_func(opstring):
		opcode_name = opstring.split('=', 1)[0]
		return OPCODE_SORT_ORDER.index(opcode_name) \
			if opcode_name in OPCODE_SORT_ORDER \
			else OPCODE_SORT_LAST
	return sorted(opstrings, key = sort_func)

def midi_note_sort_key(region):
	"""
	Provides a key to use for sorting a list of Regions based on "lokey", "hikey" values.
	"""
	key = region.key
	if key is None:
		lokey = region.lokey or 1
		hikey = region.hikey or 127
	else:
		lokey = key
		hikey = key
	return lokey * 128 + hikey

def velocity_sort_key(region):
	"""
	Provides a key to use for sorting a list of Regions based on "lovel", "hivel" values.
	"""
	hivel = float(region.hivel or 127)
	lovel = float(region.lovel or 1)
	return (hivel - lovel) / 2 + lovel


# ---------------------------
# Element classes

class Element:
	"""
	An abstract class which provides parent/child hierarchical relationship.
	This is the base class of Comment, Header, Opcode, and Define.
	"""

	_parent = None
	error = None

	def __init__(self, **kwargs):
		self.match = kwargs.get('match')
		self.comment = kwargs.get('comment')
		self._defines = kwargs.get('defines', {})

	@property
	def parent(self):
		"""
		The immediate parent Header of this element.

		If this is an SFZ, returns None. For any other type of element, returns its
		parent header, which may be the top-level SFZ.

		This attribute is set during parsing, and probably shouldn't be modified.
		"""
		return self._parent

	@parent.setter
	def parent(self, parent):
		self._parent = parent

	@property
	def sfz(self):
		"""
		Traverse up the element tree to the top-level SFZ and return it.
		"""
		element = self
		while element._parent:			# pylint: disable = protected-access
			element = element._parent	# pylint: disable = protected-access
		return element if isinstance(element, SFZ) else None

	def __repr__(self):
		return self.__class__.__name__

	def write(self, stream):
		"""
		Ouput the string representation of this Element in SFZ format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(str(self))
		if self.comment:
			stream.write(f' {self.comment}')
		stream.write(linesep)

	def clone(self):
		raise NotImplementedError()


class ExternalFile:
	"""
	Abstract class inherited by Sample and Include, which handles file path
	resolution and manipulation.
	"""

	_path = None			# Path object

	def __init__(self, path, **kwargs):
		"""
		Constructor; set "_path"
		"""
		if path is not None:
			self._path = os_any_path(path)

	@property
	def path(self):
		"""
		Returns the (pathlib.Path) path
		"""
		return self._path

	@path.setter
	def path(self, value):
		"""
		Sets the (pathlib.Path) path
		"""
		self._path = None if value is None else os_any_path(value)
		self._check()

	@property
	def abspath(self):
		"""
		Returns (pathlib.Path) the absolute path, with symlinks resolved.
		"""
		if self._path is None:
			return None
		if self._path.is_absolute():
			return self._path
		sfz = self.sfz					# pylint: disable = no-member
		if sfz is None:
			return None
		if sfz is self:
			return self._path.resolve()
		if sfz.path is None:
			return None
		dirpath = sfz.path.parent
		if default_path := self.parent.default_path:
			dirpath = dirpath / default_path
		return dirpath.joinpath(self._path).resolve()

	def exists(self):
		"""
		Returns boolean True if file exists
		"""
		abspath = self.abspath
		return False if abspath is None else abspath.exists()

	def _check(self):
		"""
		Set error if this file does not exist
		"""
		# pylint: disable-next = attribute-defined-outside-init, no-member
		self.error = None if self.exists() \
			else NotFoundError(type(self).__name__, self.abspath, self.match)


class Comment(Element):
	"""
	Encapsulates a stand-alone comment.
	"""

	def __init__(self, string, **kwargs):
		super().__init__(**kwargs)
		self.string = string

	def __str__(self):
		return self.string

	def clone(self):
		return Comment(self.string)


class Header(Element):
	"""
	An abstract class which handles the functions common to all SFZ header types.
	Each header type basically acts the same, except for checking what kind of
	subheader it may contain.
	"""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._elements = []
		self._opcodes = {}

	def clone(self):
		result = type(self)(comment = self.comment)
		for elem in self._elements:
			result.append(elem.clone())
		return result

	def may_contain(self, _):
		"""
		This function is used during parsing in order to determine if a header is a
		child of the current header, or a new subheader.
		"""
		return False

	def append_opcode(self, name, value):
		"""
		Creates an Opcode with the given name and value and adds it to this Header's
		elements list.

		Returns the appended Opcode.
		"""
		return self.append(Opcode(name, value))

	def append_subheader(self, header_name):
		"""
		Creates a Header of the given (str) "header_name" and adds it to this Header's
		elements list.

		"header_name" must be a valid header class, i.e. Global, Master, Group, Region,
		Control, Effect, Midi, or Curve.

		Returns the appended Header.
		"""
		return self.append(HEADER_CLASSES[header_name.lower()]())

	def append(self, element):
		"""
		Append an Element (Opcode, Header, Comment) to this Header.

		Returns the appended element.
		"""
		if isinstance(element, Opcode):
			self._opcodes[element.name] = element
		elif isinstance(element, Header) and not self.may_contain(element):
			raise ValueError(f'A "{self.__class__}" header ' + \
				f'may not contain a "{element.__class__}" subheader')
		self._elements.append(element)
		element.parent = self
		return element

	def remove(self, element):
		"""
		Delete the given element, if the element exists as a child of this Header or
		any of its descendants.

		Raises ValueError if the given element is not contained in this Header.
		"""
		if not self._remove(element):
			raise ValueError(f'"{element}" is not contained in "{self}"')

	def _remove(self, element):
		"""
		Called recursively from the "remove" method, this method returns True if the
		element was removed from this Header.
		"""
		if element in self._elements:
			self._elements.remove(element)
			if isinstance(element, Opcode):
				del self._opcodes[element.name]
			return True
		# pylint: disable-next = protected-access
		return any(subheader._remove(element) for subheader in self.subheaders())

	def remove_opcode(self, opcode_name):
		"""
		Delete the Opcode having the given opcode_name which is an immediate child of
		this Header.

		If this Header does not contain an Opcode having the given opcode_name, this
		method has no effect, and will not raise an error.
		"""
		if opcode_name in self._opcodes:
			self._elements.remove(self._opcodes[opcode_name])
			del self._opcodes[opcode_name]

	def remove_opcodes(self, opcode_list):
		"""
		Delete all the opcodes in the given list.

		"opcode_list" must be a list of (str) opcode names.

		If this Header does not contain any Opcode with a name given in the
		opcode_list, this method has no effect, and will not raise an error.
		"""
		for opcode_name in opcode_list:
			self.remove_opcode(opcode_name)

	@property
	def elements(self):
		"""
		Returns all elements: subheaders, comments, and opcodes.
		"""
		return self._elements

	def opcodes(self):
		"""
		Returns a dictionary of immediate children which are Opcode elements.
		"""
		return self._opcodes

	def samples(self):
		"""
		Returns all "sample" opcodes contained in this Header and all of its
		subheaders.

		This is a generator function which yields a Sample object on each iteration.
		"""
		if 'sample' in self._opcodes:
			yield self._opcodes['sample']
		for element in self._elements:
			if isinstance(element, Header):
				yield from element.samples()

	def subheaders(self):
		"""
		Returns a list of immediate children which are Header elements.
		"""
		return [ element for element in self._elements if isinstance(element, Header) ]

	def _descendants_of_type(self, cls):
		"""
		A generator function which yields an instance of the given (type) cls contained in
		this Header or any of its descendant subheaders.
		"""
		for element in self._elements:
			if isinstance(element, cls):
				yield element
			elif isinstance(element, Header):
				yield from element._descendants_of_type(cls)	# pylint: disable = protected-access

	def groups(self):
		"""
		A generator function which yields all of the <group> headers contained in this
		Header and all of its descendant subheaders.
		"""
		return self._descendants_of_type(Group)

	def regions(self):
		"""
		A generator function which yields all of the <region> headers contained in this
		Header and all of its descendant subheaders.
		"""
		return self._descendants_of_type(Region)

	def defines(self):
		"""
		A generator function which yields all of the #define directives contained in
		this Header and all of its descendant subheaders.
		"""
		return self._descendants_of_type(Define)

	def includes(self):
		"""
		A generator function which yields all of the #include directives contained in
		this Header and all of its descendant subheaders.
		"""
		return self._descendants_of_type(Include)

	def inherited_opcodes(self):
		"""
		Returns all the opcodes defined in this Header with all opcodes defined in its
		parent Header, recursively. Opcode values defined inside this Header override
		the value of the same opcode appearing in a parent Header.

		Returns dict { opcode_name:Opcode }
		"""
		return self._opcodes if self._parent is None \
			else dict(self._parent.inherited_opcodes(), **self._opcodes)

	def opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes which are used by this Header. This does NOT include opcodes
		defined in subheaders beneath this Header.
		"""
		return opcodes_to_opstrings(self._opcodes.values())

	def opstrings_used(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes used in this Header and all subheaders beneath this Header.
		"""
		opstrings = [ sub.opstrings_used() for sub in self.subheaders() ]
		opstrings.append(self.opstrings())
		return reduce(or_, opstrings, set())

	def common_opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the identical opcodes used in every subheader in this Header, including
		opcodes inherited from their parent.

		The implication of including opcodes inherited from their parent, is that in
		cases where a header defines an opcode, all the subheaders beneath that header
		will share that opcode definition as common.

		However, if one or more subheaders redefine the opcode defined in the parent
		header with a different value, that opcode will not be returned from this
		function.
		"""
		if subheaders := self.subheaders():
			sets = [ sub.common_opstrings() for sub in subheaders ]
			# At this point every element of the list is a set of opstrings, one per subheader.
			# Some subheaders have NO common sets, filter these out before reducing to a final set:
			sets = [ set_ for set_ in sets if len(set_) ]
			# Reduce to a single set, or return an empty set if all were empty.
			return reduce(and_, sets) if sets else set()
		return set(str(opcode) for opcode in self.inherited_opcodes().values())

	def opcode(self, name):
		"""
		Returns an Opcode with the given name, if one exists in this Header.

		Returns None if no such opcode exists.
		"""
		return self._opcodes[name] if name in self._opcodes else None

	def iopcode(self, name):
		"""
		Returns an Opcode with the given name, if one exists in this Header or any of
		its ancestors.

		Returns None if no such opcode exists.
		"""
		return self._opcodes[name] if name in self._opcodes \
			else None if self._parent is None \
			else self._parent.iopcode(name)

	def __getattr__(self, name):
		"""
		Returns the value of the opcode with the given "name" contained in this Header,
		or any of its ancestors.

		Raises AttributeError.
		"""
		if name[0] == '_':
			return super().__getattribute__(name)
		opcode = self.iopcode(name)
		if opcode:
			return opcode.value
		if normal_opcode(name):
			return None
		raise AttributeError(name)

	def __setattr__(self, name, value):
		"""
		Sets the value of the opcode with the given "name", if it exists.

		Creates the opcode inside this Header, if it does not yet exist.
		"""
		if name[0] == '_':
			super().__setattr__(name, value)
		elif name in self.__dict__:
			self.__dict__[name] = value
		elif '_opcodes' in self.__dict__ and name in self.__dict__['_opcodes']:
			self._opcodes[name].value = value
		elif not normal_opcode(name) is None:
			self.append(Opcode(name, value))
		else:
			super().__setattr__(name, value)

	def get_opcode_value(self, name):
		"""
		Gets the value of the opcode with the given "name", if it exists, else None.
		"""
		return self._opcodes[name].value if name in self._opcodes else None

	def set_opcode_value(self, name, value):
		"""
		Sets the value of the opcode with the given "name", if it exists.

		Creates the opcode inside this Header, if it does not yet exist.
		"""
		if name in self._opcodes:
			self._opcodes[name].value = value
		else:
			self.append(Opcode(name, value))

	def opcodes_used(self):
		"""
		Returns a set of the keys of all the opcodes used in this Header and all of
		its subheaders.
		"""
		return set(self._opcodes.keys()) | \
			reduce(or_, [ sub.opcodes_used() for sub in self.subheaders() ], set())

	def regions_for(self, *, key = None, lokey = None, hikey = None, lovel = None, hivel = None):
		"""
		Returns all <region> headers contained in this header and all of its
		subheaders which matches the given criteria.

		For example, to get every region which plays Middle C at any velocity:
			sfz.regions_for(lokey = 60, hikey = 60)

		This is a generator function which yields a Region object on each iteration.
		"""
		for region in self.regions():
			if region.is_triggered_by(key = key, lokey = lokey, hikey = hikey, lovel = lovel, hivel = hivel):
				yield region

	def clone_regions(self):
		"""
		Returns a flat list of Region headers, one for each region beneath this header.
		If this header is a Region, returns a list containing only a clone of this header.

		Each region's inherited opcodes are cloned into the new region.
		"""
		return clone_region(self) if isinstance(self, Region) \
			else [ clone_region(region) for region in self.regions() ]

	def condense_key_opcodes(self):
		"""
		Reduce "lokey", "hikey", "pitch_keycenter" opcodes to a single "key" opcode.
		"""
		key_defining_opcodes = set(self.get_opcode_value(key)
			for key in KEY_DEFINING_OPCODES
			if self.get_opcode_value(key) is not None)
		if len(key_defining_opcodes) == 1:
			self.remove_opcodes(KEY_DEFINING_OPCODES)
			self.append(Opcode('key', key_defining_opcodes.pop()))

	def remove_defaults(self):
		"""
		Remove opcodes which have the default value.

		NOTE: Be careful with this function. If a header defines an opcode value which
		is something other than the default, a contained subheader may explicity set
		the value back to the default within the subheading.
		"""
		self.remove_opcodes([
			opcode_name for opcode_name, opcode in self._opcodes.items() \
			if opcode.default_value is not None and opcode.value == opcode.default_value
		])

	def remove_unused_loops(self):
		"""
		Removes all opcodes which define loops, when the effective loop_mode is not
		looped.
		"""
		loop_mode = self.loopmode or self.loop_mode
		if loop_mode not in ('loop_continuous', 'loop_sustain'):
			self.remove_opcodes(LOOP_DEFINITION_OPCODES)

	def walk(self, depth = 0):
		"""
		Generator which recusively yields every element contained in this Header,
		including opcodes and subheaders.

		Elements are returned in the order they appear - header first, then its
		contained elements.

		Each iteration returns a tuple (Element, (int) depth)
		"""
		yield (self, depth)
		depth += 1
		for element in self._elements:
			if isinstance(element, Header):
				yield from element.walk(depth)
			else:
				yield (element, depth)

	def header_walk(self, depth = 0):
		"""
		Generator which recusively yields this header, and every subheader beneath it,
		in the order in which they appear.

		Each iteration returns a tuple consisting of a (Header) header, and (int) its
		depth in the tree, measured from this Header.
		"""
		for element, child_depth in self.walk():
			if isinstance(element, Header):
				yield element, depth + child_depth

	def reverse_header_walk(self, depth = 0):
		"""
		Generator which recusively yields this header, and every subheader beneath it,
		in reverse order. By first returning the headers deepest in the header tree, it
		allows us to modify the elements contained in a header while traversing.

		Each iteration returns a tuple consisting of a (Header) header, and (int) its
		depth in the tree, measured from this Header.
		"""
		child_depth = depth + 1
		for element in reversed(self._elements):
			if isinstance(element, Header):
				yield from element.reverse_header_walk(child_depth)
		yield (self, depth)

	def merge_includes(self):
		"""
		For every #include directive beneath this header, merge the contents of the
		referenced file into this header.

		This function operates recursively; if an included file also includes another
		file[s], those subsequent files will also be merged into the top-level SFZ.

		In order to operate recusively, this function returns the elements list
		contained in this header. When merging, calling this function forces the merged
		#include to also merge, and return a flattened element list, which is merged
		into this header's elements.
		"""
		continue_merging = True
		while continue_merging:
			continue_merging = False
			for index, element in enumerate(self._elements):
				if isinstance(element, Header):
					subelements = element.merge_includes()
					if isinstance(element, Include):
						self._elements = self._elements[:index] + \
							subelements + \
							self._elements[index + 1:]
						continue_merging = True
		self._opcodes = {
			element.name: element \
			for element in self._elements \
			if isinstance(element, Opcode) }
		return self._elements

	def __str__(self):
		return f'<{self.__class__.__name__.lower()}>'

	def __repr__(self):
		return f'{self.__class__.__name__} ({len(self._opcodes):d} opcodes)'

	def write(self, stream):
		"""
		Ouput the string representation of this Header and all of it's contained
		elements in SFZ format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(f'{linesep}{self}{linesep}')
		if self.comment:
			stream.write(f'{self.comment}{linesep}')
		for element in sorted_elements(self._elements):
			element.write(stream)


class SFZ(Header, ExternalFile):
	"""
	Provides an object-oriented interface to an .sfz file.
	"""

	errors = []

	def __init__(self, filename = None):
		"""
		Instantiate an SFZ file.

		If filename is given, parses the contents of the SFZ at the given filename.
		Otherwise, instantiates an empty SFZ file for populating programmatically.

		"filename" may be any filename-like object, including pathlib.Path or str.
		"""
		super().__init__()
		if filename:
			self.path = filename
			self._parse()

	def _parse(self):
		"""
		Parse the SFZ text and build an element tree.
		"""
		errors = []
		parser = Parser(self.abspath)
		current_header = self
		for match in parser:
			if isinstance(match, CommentMatch):
				comment = Comment(match.string, match = match)
				if current_header.elements or current_header.comment:
					current_header.append(comment)
				else:
					current_header.comment = comment
			elif isinstance(match, HeaderMatch):
				header_name = match.header_name.lower()
				if header_name in HEADER_CLASSES:
					header = HEADER_CLASSES[header_name](
						match = match, comment = match.comment)
					while not current_header.may_contain(header):
						current_header = current_header.parent
					current_header.append(header)
					current_header = header
				else:
					errors.append(InvalidHeaderError(header_name, match))
			elif isinstance(match, DefineMatch):
				define = Define(match.key, match.value,
					match = match, comment = match.comment)
				if define.error:
					errors.append(define.error)
				else:
					self._defines[define.varname] = define.value
				current_header.append(define)
			elif isinstance(match, IncludeMatch):
				include = Include(match.filename,
					match = match,
					defines = self._defines)
				current_header.append(include)
				if include.exists():
					include._parse()
				self._defines.update(include._defines)
				errors.append(include.error)		# May be NotFoundError
				errors.extend(include.errors)		# All other errors found during parsing
			elif isinstance(match, OpcodeMatch):
				opcode = Opcode(match.key, match.value,
					match = match,
					comment = match.comment,
					defines = self._defines)
				current_header.append(opcode)
				errors.append(opcode.error)
			elif isinstance(match, ParseError):
				errors.append(match)
			else:
				logging.error('Unhandled token: %s', match)
		self.errors = [ error for error in errors if not error is None ]

	def name(self):
		"""
		Returns (str) the filename of the parsed or last saved SFZ without the
		directory name or extension.
		"""
		return '[Unnamed]' if self.path is None else self.path.name

	@property
	def filename(self):
		"""
		Returns (str) path to parsed or last saved SFZ.
		"""
		return None if self.path is None else str(self.path)

	def may_contain(self, _):
		return True

	def global_header(self):
		"""
		Returns the Global header from this SFZ; it one does not exist, creates it at
		the beginning of the header list.
		"""
		for element in self._elements:
			if isinstance(element, Global):
				return element
		header = Global()
		header.parent = self
		for index, element in enumerate(self._elements):
			if not isinstance(element, Comment):
				self._elements.insert(index, header)
				break
		return header

	def save(self):
		"""
		Save to original path without any further modification.
		"""
		with open(self.path, 'w', encoding = 'utf-8') as fob:
			self.write(fob)
		return self

	def save_as(self, filename, *, samples_mode = SAMPLES_ABSPATH, overwrite = True):
		"""
		Save to the given path.

		"filename" may be any path-like object, including pathlib.Path or str.

		"samples_mode" is a constant which defines how to render "sample" opcodes.
		The value may be one of the following constants:

		Constant            File operation  New sample value
		-------------------	--------------- ------------------------
        SAMPLES_UNCHANGED   none            No change
        SAMPLES_ABSPATH     none            Absolute path to the existing sample
        SAMPLES_RELPATH     none            Relative path to the existing sample
        SAMPLES_COPY        copy            Relative path to the copy
        SAMPLES_SYMLINK     symlink         Relative path to the new symlink
        SAMPLES_HARDLINK    hardlink        Relative path to the new hardlink

		When the "samples_mode" is one of SAMPLES_COPY, SAMPLES_SYMLINK, or
		SAMPLES_HARDLINK, a directory to contain the samples is created in the same
		directory that SFZ is being saved to. The samples folder will always be named
		"<sfz name>-samples", where "<sfz name>" is the file title of the new SFZ being
		saved, minus the extension.
		"""
		new_path = os_any_path(filename)
		if new_path.suffix != '.sfz':
			new_path = new_path.with_suffix('.sfz')
		if not overwrite and new_path.exists():
			raise RuntimeError(f'File exists: "{new_path}"')
		sfz_dir = new_path.parent
		if not sfz_dir.exists():
			sfz_dir.mkdir()
		self.merge_includes()
		if samples_mode & SAMPLE_TARGET_CHANGES:
			samples_dir = sfz_dir.joinpath(new_path.stem + '-samples')
			if not samples_dir.exists():
				samples_dir.mkdir()
		if samples_mode:
			for sample in self.samples():
				if samples_mode == SAMPLES_ABSPATH:
					sample.make_absolute()
				elif samples_mode == SAMPLES_RELPATH:
					sample.make_relative(sfz_dir)
				elif samples_mode == SAMPLES_COPY:
					sample.copy_to(samples_dir, overwrite)
				elif samples_mode == SAMPLES_SYMLINK:
					sample.symlink_to(samples_dir, overwrite)
				elif samples_mode == SAMPLES_HARDLINK:
					sample.hardlink_to(samples_dir, overwrite)
		for header, _ in self.header_walk():
			header.remove_opcode('default_path')
		self.path = filename
		self.save()
		self.errors = []
		for sample in self.samples():
			if not sample.exists():
				self.errors.append(sample.error)
		return self

	def __str__(self):
		return f'<SFZ {self.filename}>'

	def simplified(self, globalize_numerous = True):
		"""
		Returns an equivalent SFZ with common opcodes grouped, and opcodes using the
		default value skipped.
		"""
		simplified_sfz = SFZ()
		global_header = Global()
		regions = self.clone_regions()

		for region in regions:
			region.remove_defaults()
			region.remove_unused_loops()

		# Place opcodes which have the same value in a majority of regions
		# into the global header:
		if globalize_numerous and len(regions) > 1:
			opstring_counts = defaultdict(int)
			for region in regions:
				for opstring in region.opstrings():
					opstring_counts[opstring] += 1
			min_count = ceil(len(regions) / 2)
			remove_dict = opstrings_to_dict([
				opstring for opstring, count in opstring_counts.items() \
				if count >= min_count ])
			for opcode_name, opcode_value in remove_dict.items():
				if opcode_name not in KEY_DEFINING_OPCODES:
					global_header.append(Opcode(opcode_name, opcode_value))
					for region in regions:
						if str(region.get_opcode_value(opcode_name)) == opcode_value:
							region.remove_opcode(opcode_name)

		for region in regions:
			region.condense_key_opcodes()

		# Sort in key order:
		regions.sort(key = midi_note_sort_key)

		# Group regions based on common key:
		for group in key_group_regions(regions):
			if group.opstrings_used():
				simplified_sfz.append(group)

		if len(global_header.opcodes()):
			simplified_sfz.elements.insert(0, global_header)
			global_header.parent = simplified_sfz

		simplified_sfz.path = self.path.parent.joinpath(self.path.stem + '-simplified.sfz')
		return simplified_sfz

	def dump(self):
		"""
		Print a concise outline of this SFZ to stdout.
		"""
		for element, depth in self.walk():
			print('  ' * depth + repr(element))

	def write(self, stream):
		"""
		Ouput the string representation of this SFZ and all of it's contained
		elements in SFZ format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(f'// {self.name()}{linesep}')
		if self.comment:
			stream.write(f'{self.comment}{linesep}')
		for element in sorted_elements(self._elements):
			element.write(stream)


class Global(Header):
	"""
	Represents an SFZ Global header.
	"""

	def may_contain(self, _):
		return True


class Master(Header):
	"""
	Represents an SFZ Master header.
	"""

	def may_contain(self, header):
		return type(header) not in [Global, Master]


class Group(Header):
	"""
	Represents an SFZ Group header.
	"""

	def may_contain(self, header):
		return type(header) not in [Global, Master, Group]


class Region(Header):
	"""
	Represents an SFZ Region header.
	"""

	def may_contain(self, header):
		"""
		Used during parsing to determine where to append a newly parsed Header
		"""
		return type(header) not in [Global, Master, Group, Region]

	def is_triggered_by(self, *, key = None, lokey = None, hikey = None, lovel = None, hivel = None):
		"""
		Returns boolean True/False if this Region matches the given criteria.

		For example, to test if this region plays Middle C at any velocity:

			if region.is_triggered_by(key = 60):
				[...]
		"""
		if key is None and lokey is None and hikey is None and lovel is None and hivel is None:
			raise RuntimeError('Requires a key or velocity to test against')
		ops = self.inherited_opcodes()
		if key is not None:
			if lokey is not None:
				logging.warning(
					'You should provide either "key" or "lokey" but not both ("key" takes precedence)')
			if hikey is not None:
				logging.warning(
					'You should provide either "key" or "hikey" but not both ("key" takes precedence)')
			if 'key' in ops and ops['key'].value != key:
				return False
			lokey = key
			hikey = key
		if lokey is not None and 'lokey' in ops and ops['lokey'].value > lokey:
			return False
		if hikey is not None and 'hikey' in ops and ops['hikey'].value < hikey:
			return False
		if lovel is not None and 'lovel' in ops and ops['lovel'].value > lovel:
			return False
		if hivel is not None and 'hivel' in ops and ops['hivel'].value < hivel:
			return False
		return True


class Control(Header):
	"""
	Represents an SFZ Control header.
	"""


class Effect(Header):
	"""
	Represents an SFZ Effect header.
	"""


class Midi(Header):
	"""
	Represents an SFZ MIDI header.
	"""


class Curve(Header):
	"""
	Represents an SFZ curve.
	"""

	curve_index = None
	points = {}

	def __str__(self):
		return f'<curve>curve_index={self.curve_index}'

	def write(self, stream):
		"""
		Ouput the string representation of this Curve and all of it's points in SFZ
		format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(f'{self}{linesep}')
		for key, val in self.points.items():
			stream.write(f'{key}={val}{linesep}')


class Opcode(Element):
	"""
	Represents an SFZ opcode.
	"""

	_name = None
	_given_name = None
	_given_value = None
	_value = None

	def __new__(cls, name, value, **kwargs):
		return super().__new__(Sample) if name.lower() == 'sample' else super().__new__(Opcode)

	def __init__(self, name, value, **kwargs):
		"""
		"name" is a (str) opcode name, before normalizing.
		"value" is the assigned value. When parsing, this is always a string.

		Keyword arguments:

		"match" is a ParserMatch returned by sfzen.Parser.
		"comment" is a Comment element associated with this element.
		"defines" is a dict of variables defined in the SFZ.

		All of these arguments are passed to the constructor during parsing of an
		existing SFZ file. You can safely ignore them when constructing an SFZ from
		scratch.
		"""
		super().__init__(**kwargs)
		self._given_name = name
		self._name = replace_defs(name, self._defines)
		self.validator = Validator.get_validator(self._name)	# set before setting "value"
		self.value = value	# Using property setting forces validation

	def clone(self):
		return Opcode(self._name, self._value, comment = self.comment)

	@property
	def name(self):
		"""
		Returns the value as the type defined in the opcode definition.
		"""
		return self._name

	@property
	def value(self):
		"""
		Returns the value as the type defined in the opcode definition.
		"""
		return self._value

	@value.setter
	def value(self, value):
		"""
		Set the value of this Opcode, after converting the given "value" to
		the appropriate data type and checking if valid.
		"""
		self._given_value = value
		if value is None:
			self._value, self.error = None,	None
		else:
			self._value, self.error = self.validator.check_value(
				replace_defs(value, self._defines), self.match)

	@property
	def given_value(self):
		"""
		Returns the value given (as during parsing), without modification
		"""
		return self._given_value

	@cached_property
	def default_value(self):
		"""
		Returns the default value as the type defined in the opcode definition.
		"""
		return self.validator.default_value

	@cached_property
	def type_str(self):
		"""
		Returns the string "var_type" defined in the opcode definition.
		"""
		return self.validator.type_str

	@cached_property
	def unit(self):
		"""
		Returns the unit defined in the opcode definition.
		"""
		return self.validator.unit

	@cached_property
	def definition(self):
		"""
		Returns the defintion of this opcode from the SFZ syntax (see opcodes.py)
		The defintion name is normalized, replacing "_ccN" -type elements.
		"""
		return opcode_definition(self._name)

	def __str__(self):
		return f'{self._name}={self._value}'

	def __repr__(self):
		return f'{self.__class__.__name__} {self}'


class Sample(Opcode, ExternalFile):
	"""
	Unique case Opcode with extra functions for path manipulation.
	"""

	def __init__(self, name, value, **kwargs):
		"""
		When instantiating a Sample, the "name" is always "sample" and the "value"
		should be the path to the sample as it appears in the SFZ.
		"""
		ExternalFile.__init__(self, value, **kwargs)
		Opcode.__init__(self, name, value, **kwargs)

	def clone(self):
		return Sample(self._name, self.abspath, comment = self.comment)

	@Opcode.value.setter
	def value(self, value):
		self._given_value = value
		self._value = replace_defs(str(value), self._defines)
		self.path = os_any_path(self._value)

	@Element.parent.setter
	def parent(self, parent):
		self._parent = parent
		self._check()

	def write(self, stream):
		"""
		Ouput the string representation of this Sample in SFZ format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(str(self))
		if self.comment:
			stream.write(f' {self.comment}')
		stream.write(linesep)

	def make_absolute(self):
		"""
		Make the "value" of this element an absolute path.
		"""
		self._value = str(self.abspath)
		self.path = os_any_path(self._value)

	def make_relative(self, sfz_dir):
		"""
		Make the "value" of this element a path relative to its previous path.
		"""
		self._value = relpath(self.abspath, sfz_dir.absolute())
		self.path = self._value

	def copy_to(self, samples_dir, overwrite):
		"""
		Copy the sample file to a new location and update the "value" of this sample to
		a path relative to the new sfz path.

		"samples_dir" is a Path to the directory where the samples are to be written.
		"""
		new_path = self._new_target(samples_dir, overwrite)
		copyfile(self.abspath, new_path)
		self._update_path(samples_dir, new_path)

	def move_to(self, samples_dir, overwrite):
		"""
		Move the sample file to a new location and update the "value" of this sample to
		a path relative to the new sfz path.

		"samples_dir" is a Path to the directory where the samples are to be written.
		"""
		new_path = self._new_target(samples_dir, overwrite)
		move(self.abspath, new_path)
		self._update_path(samples_dir, new_path)

	def symlink_to(self, samples_dir, overwrite):
		"""
		Create a symlink to the original sample inside a new samples directory,
		relative to the new sfz path.

		"samples_dir" is a Path to the directory where the samples are to be written.
		"""
		new_path = self._new_target(samples_dir, overwrite)
		new_path.symlink_to(self.abspath)
		self._update_path(samples_dir, new_path)

	def hardlink_to(self, samples_dir, overwrite):
		"""
		Create a hardlink to the original sample inside a new samples directory,
		relative to the new sfz path.

		"samples_dir" is a Path to the directory where the samples are to be written.
		"""
		new_path = self._new_target(samples_dir, overwrite)
		self.abspath.link_to(new_path)
		self._update_path(samples_dir, new_path)

	def _new_target(self, samples_dir, overwrite):
		"""
		Returns (pathlib.Path) the target of a copy/move/symlink/hardlink op.
		"""
		new_path = samples_dir / self.path.name
		if new_path.exists():
			if overwrite:
				new_path.unlink()
			else:
				raise RuntimeError(f'File exists: "{new_path}"')
		return new_path

	def _update_path(self, samples_dir, new_path):
		"""
		Updates this Sample's "path" attribute after a copy/move/symlink/hardlink.
		"""
		self._path = new_path.relative_to(samples_dir.parent)
		self._given_value = str(self.path)
		self._value = self._given_value
		self._check()


class Define(Element):
	"""
	Represents a variable definition (SFZ "#define $<key> <value>").

	Note on defines: Using liquidsfz, I did an experiment to find out if a define
	was local to it's containing header. Meaning, if a define sets the value of a
	variable, and then another define in a subheader overwrites that value, will
	the value reset to the original when leaving the subheader.

	Apparently not. It appears that the LAST value of a variable set with #define
	is used, regardless of where it is set.

	"""

	def __init__(self, varname, value, **kwargs):
		super().__init__(**kwargs)
		self.varname = varname
		self.value = value

	def clone(self):
		return Define(self.varname, self.value, comment = self.comment)

	def __str__(self):
		return f'#define ${self.varname} {self.value}'


class Include(SFZ):
	"""
	Represents an Include Opcode.
	"""

	# pylint: disable-next = super-init-not-called
	def __init__(self, value, **kwargs):
		# pylint: disable-next = non-parent-init-called
		Header.__init__(self, **kwargs)
		# pylint: disable-next = non-parent-init-called
		ExternalFile.__init__(self, value, **kwargs)
		if self.exists():
			self._parse()

	@Element.parent.setter
	def parent(self, parent):
		self._parent = parent
		self._check()

	@property
	def value(self):
		"""
		Returns the value as the type defined in the opcode definition.
		"""
		return str(self.path)

	@value.setter
	def value(self, value):
		self.path = value

	def clone(self):
		return Include(self.path, comment = self.comment)

	def __str__(self):
		return f'#include "{self.path}"'

	def write(self, stream):
		"""
		Ouput the string representation of this SFZ and all of it's contained
		elements in SFZ format.

		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(f'{linesep}{self}{linesep}{linesep}')
		for element in self._elements:
			element.write(stream)


# ---------------------------
# Validator classes

class Validator:
	"""
	Abstract base class of the various validator classes.
	"""

	validators = {}

	@classmethod
	def get_validator(cls, opcode_name):
		"""
		Returns an instance of the Validator class appropriate for the given opcode_name.
		"""
		def _instantiate_validator(normal_name):
			value_def = value_definition(normal_name)
			if normal_name in KEY_TYPE_OPCODES:
				return PitchValidator(normal_name, value_def)
			if value_def is None:
				return AnyValidator(normal_name, value_def)
			if value_def[K_CHOICES]:
				return ChoiceValidator(normal_name, value_def)
			if not value_def[K_MIN] is None:
				return MinValidator(normal_name, value_def) \
					if value_def[K_MAX] is None or value_def[K_MAX] == 'SampleRate / 2' \
					else RangeValidator(normal_name, value_def)
			return AnyValidator(normal_name, value_def) \
				if value_def[K_VAR_TYPE] is None \
				else TypeValidator(normal_name, value_def)
		normal_name = normal_opcode(opcode_name)
		if normal_name is None:
			return InvalidOpcodeValidator(opcode_name)
		if normal_name not in cls.validators:
			cls.validators[normal_name] = _instantiate_validator(normal_name)
		return cls.validators[normal_name]

	def __init__(self, opcode_name, value_def):
		self.opcode_name = opcode_name
		self.value_def = value_def
		if self.value_def[K_VAR_TYPE] == 'str':
			self._check_type = self.__check_str
		elif self.value_def[K_VAR_TYPE] == 'int':
			self._check_type = self.__check_int
		elif self.value_def[K_VAR_TYPE] == 'float':
			self._check_type = self.__check_float

	# pylint: disable-next = method-hidden
	def _check_type(self, value, _):
		"""
		Checks and coerces a value and returns a tuple containing:
			The value coerced to the correct var type,
			Any validation error, or None if no error

		This function is replaced by one of the "_check_<var_type>" funcs when
		appropriate for the given opcode.
		"""
		return value, None

	def __check_str(self, value, _):
		"""
		Validates returns the value coerced to str.
		"""
		return str(value), None

	def __check_int(self, value, match):
		"""
		Validates an int and returns the value coerced to int.
		"""
		if isinstance(value, int):
			return value, None
		if isinstance(value, str) and INT_VALIDATOR_REGEX.match(value):
			return int(value), None
		return value, DataTypeError(self.opcode_name, value, match)

	def __check_float(self, value, match):
		"""
		Validates a float and returns the value coerced to float.
		"""
		try:
			return float(value), None
		except ValueError:
			return value, DataTypeError(self.opcode_name, value, match)

	def _type_class(self):
		if self.value_def[K_VAR_TYPE] == 'int':
			return int
		if self.value_def[K_VAR_TYPE] == 'float':
			return float
		return str

	@property
	def default_value(self):
		"""
		Returns the default value as the type defined in the opcode definition.
		"""
		if self.value_def[K_DEFAULT] is None:
			return None
		type_ = self._type_class()
		return type_(self.value_def[K_DEFAULT])

	@property
	def type_str(self):
		"""
		Returns the "var_type" string defined in the opcode definition.
		"""
		return self.value_def[K_VAR_TYPE]

	@property
	def unit(self):
		"""
		Returns the unit defined in the opcode definition.
		"""
		return self.value_def[K_UNIT]


class AnyValidator(Validator):
	"""
	Validates an opcode when any value is valid.
	"""

	def check_value(self, value, _):
		"""
		This class allows all values, and does not coerce.
		"""
		return value, None


class TypeValidator(Validator):
	"""
	Validates an opcode when valid values are in a predefined list of choices.
	"""

	def check_value(self, value, match):
		"""
		This class only checks the data type.
		"""
		return self._check_type(value, match)


class ChoiceValidator(Validator):
	"""
	Validates an opcode when valid values are in a predefined list of choices.
	"""

	def __init__(self, opcode_name, value_def):
		super().__init__(opcode_name, value_def)
		self.choices = [ int(choice[K_NAME]) for choice in value_def[K_CHOICES] ] \
			if value_def[K_VAR_TYPE] == 'int' \
			else [ choice[K_NAME] for choice in value_def[K_CHOICES] ]

	def check_value(self, value, match):
		value, err = self._check_type(value, match)
		if err:
			return value, err
		if not str(value) in self.choices:
			return value, ChoiceError(self.opcode_name, value, match)
		return value, None


class MinValidator(Validator):
	"""
	Validates an opcode when valid values are from a set minimum to any upper value.
	"""

	def __init__(self, opcode_name, value_def):
		super().__init__(opcode_name, value_def)
		type_ = self._type_class()
		if not isinstance(type_, (float, int)):
			type_ = float
		self.min = type_(value_def[K_MIN])

	def check_value(self, value, match):
		value, err = self._check_type(value, match)
		if err:
			return value, err
		if value < self.min:
			return value, MinError(self.opcode_name, value, self.min, match)
		return value, None


class RangeValidator(Validator):
	"""
	Validates an opcode when valid values are within a range.
	"""

	def __init__(self, opcode_name, value_def):
		super().__init__(opcode_name, value_def)
		type_ = self._type_class()
		if not isinstance(type_, (float, int)):
			type_ = float
		self.min = type_(value_def[K_MIN])
		self.max = type_(value_def[K_MAX])

	def check_value(self, value, match):
		value, err = self._check_type(value, match)
		if err:
			return value, err
		if value < self.min:
			return value, MinError(self.opcode_name, value, self.min, match)
		if value > self.max:
			return value, MaxError(self.opcode_name, value, self.max, match)
		return value, None


class PitchValidator(Validator):
	"""
	Special purpose validator which handles named keys (i.e. "C3", "B#4").
	"""

	# pylint: disable-next = super-init-not-called
	def __init__(self, opcode_name, value_def):
		self.opcode_name = opcode_name
		self.value_def = value_def

	def check_value(self, value, match):
		"""
		Verifies that the given value is an integer in the range 0-127, or a named note.
		"""
		try:
			note = Note(value, interpret_freq = False)
		except NoteValueError:
			return value, DataTypeError(self.opcode_name, value, match)
		return note.pitch, None


class InvalidOpcodeValidator(Validator):
	"""
	Special purpose validator which always returns an InvalidOpcodeError
	"""

	# pylint: disable-next = super-init-not-called
	def __init__(self, opcode_name):
		self.opcode_name = opcode_name

	def check_value(self, value, match):
		return value, InvalidOpcodeError(self.opcode_name, match)


# ---------------------------
# Validation error classes

class ValidationError(Exception):
	"""
	Abstract base class of all errors raised in opcode value validation.
	"""

	def __init__(self, match, message):
		self.match = match
		self.origin = message
		super().__init__(message if match is None else \
			f'line {match.line}, char {match.start}: {message}')


class DataTypeError(ValidationError):
	"""
	Custom exception raised when value cannot be cast as an opcode's data type
	"""

	def __init__(self, opcode_name, value, match):
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Value [{value}] is of the incorrect type for "{opcode_name}"')


class MinError(ValidationError):
	"""
	Custom exception raised when value is below min
	"""

	def __init__(self, opcode_name, value, min_, match):
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Value [{value}] is below the minimum [{min_}] for "{opcode_name}"')


class MaxError(ValidationError):
	"""
	Custom exception raised when value is above max
	"""

	def __init__(self, opcode_name, value, max_, match):
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Value [{value}] is above the maximum [{max_}] for "{opcode_name}"')


class ChoiceError(ValidationError):
	"""
	Custom exception raised when value is not a valid choice
	"""

	def __init__(self, opcode_name, value, match):
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Value [{value}] is not a valid choice for "{opcode_name}"')


class NotFoundError(ValidationError):
	"""
	Custom exception raised when a referenced file (sample or include) is not found
	on disk.
	"""

	def __init__(self, opcode_name, value, match):
		"""
		opcode_name will be one of: "include" or "sample",
		"""
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Referenced "{opcode_name}" [{value}] not found')


class InvalidOpcodeError(ValidationError):
	"""
	Custom exception raised when an unrecognized <header> tag is found.
	"""

	def __init__(self, opcode_name, match):
		self.opcode_name = opcode_name
		super().__init__(match,
			f'Invalid opcode name "{opcode_name}"')


class InvalidHeaderError(ValidationError):
	"""
	Custom exception raised when an unrecognized <header> tag is found.
	"""

	def __init__(self, header_name, match):
		self.header_name = header_name
		super().__init__(match,
			f'Invalid header name "{header_name}"')



# ---------------------------
# Class name / class lookup
# (Note: must follow class defs)

HEADER_CLASSES = {
	'global':	Global,
	'master':	Master,
	'group':	Group,
	'region':	Region,
	'control':	Control,
	'effect':	Effect,
	'midi':		Midi,
	'curve':	Curve
}


#  end sfzen/__init__.py
