#  sfzen/sfz_elems.py
#
#  Copyright 2024 liyang <liyang@veronica>
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
Classes which are instantiated when parsing an .sfz file.
All of these classes are constructed from a lark parser tree Token.
"""
import re, logging
from os import unlink, symlink, link as hardlink, sep as path_separator
from os.path import abspath, exists, islink, join, relpath, realpath
from shutil import move, copy2 as copy
from functools import cached_property, reduce
try:
	from functools import cache
except ImportError:
	from functools import lru_cache as cache
from operator import and_, or_
from midi_notes import NOTE_PITCHES
from sfzen.sort import opcode_sorted
from sfzen.opcodes import OPCODES


# ---------------------------
# Elements

class _SFZElement:
	"""
	An abstract class which provides parent/child hierarchical relationship.
	This is the base class of all Headers and Opcodes.
	"""

	def __init__(self, meta):
		if meta is None:
			self.line = None
			self.column = None
			self.end_line = None
			self.end_column = None
		else:
			self.line = meta.line
			self.column = meta.column
			self.end_line = meta.end_line
			self.end_column = meta.end_column
		self._parent = None

	@property
	def parent(self):
		"""
		The immediate parent of this element.
		If this is an SFZ, returns None.
		For any other type of element, returns its parent header, or the SFZ if this is
		a top-level header.
		This attribute is set during parsing, and probably shouldn't be modified,
		unless you really know what you are doing.
		"""
		return self._parent

	@parent.setter
	def parent(self, parent):
		self._parent = parent

	def __repr__(self):
		return type(self).__name__


class Header(_SFZElement):
	"""
	An abstract class which handles the functions common to all SFZ header types.
	Each header type basically acts the same, except for checking what kind of
	subheader it may contain.
	"""

	def __init__(self, meta = None):
		super().__init__(meta)
		self._subheaders = []
		self._opcodes = {}

	def may_contain(self, _):
		"""
		This function is used to determine if a header being parsed is a child of the
		last previous header, or the start of an entirely new header group.
		"""
		return False

	def append_opcode(self, opcode):
		"""
		Append an opcode to this Header.

		Returns the appended opcode.
		"""
		self._opcodes[opcode.name] = opcode
		opcode.parent = self
		return opcode

	def append_subheader(self, subheader):
		"""
		Append a subheader to this Header.

		Returns the appended subheader.
		"""
		self._subheaders.append(subheader)
		subheader.parent = self
		return subheader

	@property
	def opcodes(self):
		"""
		Returns a dictionary of Opcode ojects.
		Returns dict { opcode_name:Opcode }
		"""
		return self._opcodes

	@property
	def subheaders(self):
		"""
		Returns a list of headers contained in this Header.
		"""
		return self._subheaders

	def inherited_opcodes(self):
		"""
		Returns all the opcodes defined in this Header with all opcodes defined in its
		parent Header, recursively. Opcodes defined in this Header override parents'.
		Returns dict { opcode_name:Opcode }
		"""
		return self._opcodes if self._parent is None \
			else dict(self._parent.inherited_opcodes(), **self._opcodes)

	def opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes which are used by this Header. This does NOT include opcodes
		used by subheaders beneath this Header.
		"""
		return set(str(opcode) for opcode in self._opcodes.values())

	def opstrings_used(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes used in this Header, and any subheaders beneath this Header.
		"""
		opstrings = [sub.opstrings_used() for sub in self._subheaders]
		opstrings.append(self.opstrings())
		return reduce(or_, opstrings, set())

	def common_opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the identical opcodes used in every subheader in this Header.
		"""
		if self._subheaders:
			sets = [ sub.common_opstrings() for sub in self._subheaders ]
			# At this point every element of the list is a set of opstrings, one per subheader.
			# Some subheaders have NO common sets, filter these out before reducing to a final set:
			sets = [ set_ for set_ in sets if len(set_) ]
			# Reduce to a single set, or return an empty set if all were empty.
			return reduce(and_, sets) if sets else set()
		return set(str(opcode) for opcode in self.inherited_opcodes().values())

	def uses_opstring(self, opstring):
		"""
		Returns True if the given string representation (including name and value) of
		an opcode is used by this Header. This does not include opcodes used by
		_Headers contained in this Header.
		"""
		return opstring in self.opstrings()

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

		Raises AttributeError
		"""
		try:
			return super().__getattribute__(name)
		except AttributeError as err:
			opcode = self.iopcode(name)
			if opcode:
				return opcode.value
			if normal_opcode(name):
				return None
			raise err

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
			self.append_opcode(Opcode(name, value, None))
		else:
			super().__setattr__(name, value)

	def opcodes_used(self):
		"""
		Returns a set of the keys of all the opcodes used in this Header and all of
		its subheaders.
		"""
		return set(self._opcodes.keys()) | reduce(or_, [sub.opcodes_used() \
			for sub in self._subheaders], set())

	def regions(self):
		"""
		Returns all <region> headers contained in this Header and all of its
		subheaders.
		This is a generator function which yields a Region object on each iteration.
		"""
		for sub in self._subheaders:
			if isinstance(sub, Region):
				yield sub
			yield from sub.regions()

	def samples(self):
		"""
		This is a generator function which yields a Sample object on each iteration.
		"""
		if 'sample' in self._opcodes:
			yield self._opcodes['sample']
		for sub in self._subheaders:
			yield from sub.samples()

	def walk(self, depth = 0):
		"""
		Generator which recusively yields every element contained in this Header,
		including opcodes and subheaders. Opcodes are yielded first, then subheaders.
		Each iteration returns a tuple (_SFZElement, (int) depth)
		"""
		yield (self, depth)
		depth += 1
		for opcode in self._opcodes.values():
			yield (opcode, depth)
		for sub in self._subheaders:
			yield from sub.walk(depth)

	def opcode_count(self):
		"""
		Returns (int) number of opcodes used in this Header and all subheaders
		"""
		return sum(len(elem.opcodes.values()) \
			for elem, _ in self.walk() \
			if isinstance(elem, Header))

	def reduce_common_opcodes(self):
		"""
		Move common opcodes (name/value) from contained headers to this header.
		"""
		if self._subheaders:
			common_opstrings = self.common_opstrings()
			for tup in [ opstring.split('=', 1) for opstring in common_opstrings ]:
				self.append_opcode(Opcode(tup[0], tup[1]))
				for sub in self._subheaders:
					del sub._opcodes[tup[0]]

	def remove_opcodes(self, opcode_list):
		for elem, _ in self.walk():
			if isinstance(elem, Header):
				elem._opcodes = { key:opcode \
					for key, opcode in elem._opcodes.items() \
					if key not in opcode_list }

	def __str__(self):
		return '<%s>' % type(self).__name__.lower()

	def __repr__(self):
		return '{0} ({1:d} opcodes)'.format(type(self).__name__, len(self._opcodes))

	def write(self, stream):
		"""
		Exports this Header and all of it's contained headers and
		opcodes to .sfz format.
		"stream" may be any file-like object, like "sys.stdout".
		"""
		stream.write(str(self) + "\n")
		if self._opcodes:
			for op in opcode_sorted(self._opcodes.values()):
				op.write(stream)
			stream.write("\n")
		if self._subheaders:
			for sub in self._subheaders:
				sub.write(stream)


class _Modifier(_SFZElement):
	pass


class Global(Header):
	"""
	Represents an SFZ Global header. Created by Lark transformer when importing SFZ.
	"""

	def may_contain(self, _):
		return True


class Master(Header):
	"""
	Represents an SFZ Master header. Created by Lark transformer when importing SFZ.
	"""

	def may_contain(self, header):
		return type(header) not in [Global, Master]


class Group(Header):
	"""
	Represents an SFZ Group header. Created by Lark transformer when importing SFZ.
	"""

	def may_contain(self, header):
		return type(header) not in [Global, Master, Group]


class Region(Header):
	"""
	Represents an SFZ Region header. Created by Lark transformer when importing SFZ.
	"""

	def may_contain(self, header):
		"""
		Used during parsing to determine where to append a newly parsed Header
		"""
		return type(header) not in [Global, Master, Group, Region]

	def is_triggerd_by(self, key=None, lokey=None, hikey=None, lovel=None, hivel=None):
		"""
		Returns boolean True/False if this Region matches the given criteria.
		For example, to test if this region plays Middle C at any velocity:
			region.is_triggerd_by(lokey = 60, hikey = 60)
		"""
		if key is None and lokey is None and hikey is None and lovel is None and hivel is None:
			raise Exception('Requires a key or velocity to test against')
		ops = self.inherited_opcodes()
		if key is not None and 'key' in ops and ops['key'].value != key:
			return False
		if lokey is not None and 'lokey' in ops and ops['lokey'].value > lokey:
			return False
		if hikey is not None and 'hikey' in ops and ops['hikey'].value < hikey:
			return False
		if lovel is not None and 'lovel' in ops and ops['lovel'].value > lovel:
			return False
		if hivel is not None and 'hivel' in ops and ops['hivel'].value < hivel:
			return False
		return True

	@property
	def sample(self):
		"""
		Returns the Sample opcode contained in this <region>
		Returns None if no Sample has yet defined.
		"""
		return self._


class Control(Header):
	"""
	Represents an SFZ Control header. Created by Lark transformer when importing SFZ.
	"""


class Effect(Header):
	"""
	Represents an SFZ Effect header. Created by Lark transformer when importing SFZ.
	"""


class Midi(Header):
	"""
	Represents an SFZ MIDI header. Created by Lark transformer when importing SFZ.
	"""


class Curve(Header):
	"""
	Represents an SFZ curve. Created by Lark transformer when importing SFZ.
	"""

	curve_index = None
	points = {}

	def __str__(self):
		return '<%s>curve_index=%s' % (type(self).__name__.lower(), self.curve_index)

	def write(self, stream):
		"""
		Exports this Curve to .sfz format.
		"stream" may be any file-like object, including sys.stdout.
		"""
		stream.write(str(self) + "\n")
		for vals in self.points.items():
			stream.write('%s=%s\n' % vals)


class Opcode(_SFZElement):
	"""
	Represents an SFZ opcode. Created by Lark transformer when importing SFZ.
	"""

	def __new__(cls, name, value, meta = None, basedir = None):
		return super().__new__(Sample) if name == 'sample' else super().__new__(Opcode)

	def __init__(self, name, value, meta = None, *_):
		super().__init__(meta)
		self.name = name
		self.value = value

	@property
	def value(self):
		"""
		Returns the value as the type defined in the opcode definition.
		"""
		return self._value

	@value.setter
	def value(self, value):
		"""
		Converts the given value to the type defined in the opcode definition.
		"""
		if self.type is float:
			self._value = float(value)
		elif self.type == int:
			try:
				self._value = int(value)
			except ValueError as err:
				if value.upper() in NOTE_PITCHES:
					self._value = NOTE_PITCHES[value.upper()]
				else:
					raise err
		else:
			self._value = value

	@cached_property
	def type(self):
		return data_type(self.name)

	@cached_property
	def type_str(self):
		"""
		Returns the string "type" defined in the opcode definition.
		"""
		return self._def_value('type')

	@cached_property
	def unit(self):
		"""
		Returns the unit defined in the opcode definition.
		"""
		return self._def_value('unit')

	@cached_property
	def validation_rule(self):
		"""
		Returns the validation rule defined in the opcode definition.
		"""
		return self._def_value('valid')

	@cached_property
	def validator(self):
		"""
		Returns a class which extends _Validator
		"""
		return validator_for(self.name)

	@cached_property
	def definition(self):
		"""
		Returns the defintion of this opcode from the SFZ syntax (see opcodes.py)
		The defintion name is normalized, replacing "_ccN" -type elements.
		"""
		return opcode_definition(self.name)

	def _def_value(self, key):
		"""
		Returns the attribute of the opcode defintion specified by the given "key".
		If there is no opcode definition found, returns None.
		"""
		return None \
			if self.definition is None or 'value' not in self.definition \
			else self.definition['value'][key]

	def __str__(self):
		return '%s=%s' % (self.name, self._value)

	def __repr__(self):
		return f'Opcode {self}'

	def write(self, stream):
		"""
		Exports this Opcode to .sfz format.
		"stream" may be any file-like object, (including sys.stdout).
		"""
		stream.write(str(self) + "\n")


class Sample(Opcode):
	"""
	Unique case Opcode with extra functions for path manipulation.
	"""

	RE_PATH_DIVIDER = '[\\\/]'

	def __init__(self, name, value, meta = None, basedir = None):
		"""
		When instantiating a Sample, the "name" is always "Sample"; the "value"
		is the path to the sample as it appears in the SFZ. In Opcode.__init__(),
		the internal "_value" property is set to the given value.

		The "meta" argument is passed to the constructor during parsing of an existing
		SFZ file. You can safely ignore it when constructing an SFZ from scratch.

		"basedir" would be the name of the directory containing the SFZ which owns this
		Sample. This value is used for determing the relative path to a sample defined
		with an absolute path.
		"""
		super().__init__(name, value, meta)
		self.basedir = basedir

	@property
	def _path_parts(self):
		"""
		Splits the directory / filenames of the parsed value of this opcode
		Returns list of str
		"""
		return re.split(self.RE_PATH_DIVIDER, self._value)

	@property
	def abspath(self):
		"""
		Returns (str) the absolute path to the sample
		"""
		path = path_separator + join(*self._path_parts)
		return path if exists(path) else abspath(join(self.basedir, *self._path_parts))

	@property
	def basename(self):
		"""
		Returns (str) the basename of the sample
		"""
		return self._path_parts[-1]

	def exists(self):
		"""
		Returns boolean True if file exists
		"""
		return exists(self.abspath)

	def use_abspath(self):
		"""
		Directs this Sample to use an absolute path when writing .sfz
		"""
		self._value = self.abspath

	def _new_target(self, sfz_directory, samples_path):
		"""
		Returns a tuple ((str) value, (str) abspath),
		where "value" is the new opcode value for this Sample, and
		"abspath" is the target of a copy/move/symlink/hardlink op.
		"""
		return (
			join(samples_path, self.basename),
			join(sfz_directory, samples_path, self.basename)
		)

	def resolve_from(self, sfz_directory):
		"""
		Directs this Sample to use a relative path when writing .sfz.

		"sfz_directory" is the directory in which the .sfz file is to be written.
		"""
		self._value = relpath(realpath(self.abspath), realpath(sfz_directory))

	def copy_to(self, sfz_directory, samples_path):
		"""
		Copies the source sample to a new location and sets the value of this "sample"
		opcode to point to the new location.

		"sfz_directory" is the directory in which the .sfz file is to be written.

		"samples_path" is the directory where the samples are to be written, relative
		to "sfz_directory".
		"""
		value, path = self._new_target(sfz_directory, samples_path)
		if exists(path):
			unlink(path)
		copy(self.abspath, path)
		self._value = value

	def move_to(self, sfz_directory, samples_path):
		"""
		Moves the source sample to a new location and sets the value of this "sample"
		opcode to point to the new location.

		"sfz_directory" is the directory in which the .sfz file is to be written.

		"samples_path" is the directory where the samples are to be written, relative
		to "sfz_directory".
		"""
		value, path = self._new_target(sfz_directory, samples_path)
		if exists(path):
			unlink(path)
		move(self.abspath, path)
		self._value = value

	def symlink_to(self, sfz_directory, samples_path):
		"""
		Symlinks the source sample in a new samples directory and sets the value of
		this "sample" opcode to point to the new location.

		"sfz_directory" is the directory in which the .sfz file is to be written.

		"samples_path" is the directory where the samples are to be written, relative
		to "sfz_directory".
		"""
		value, path = self._new_target(sfz_directory, samples_path)
		if exists(path):
			unlink(path)
		symlink(realpath(self.abspath), realpath(path))
		self._value = value

	def hardlink_to(self, sfz_directory, samples_path):
		"""
		Hard links the source sample in a new samples directory and sets the value of
		this "sample" opcode to point to the new location.

		"sfz_directory" is the directory in which the .sfz file is to be written.

		"samples_path" is the directory where the samples are to be written, relative
		to "sfz_directory".
		"""
		value, path = self._new_target(sfz_directory, samples_path)
		if exists(path):
			unlink(path)
		hardlink(self.abspath, path)
		self._value = value


class Define(_Modifier):
	"""
	Represents a Define Opcode. Created by Lark transformer when importing SFZ.
	"""

	def __init__(self, varname, value, meta):
		super().__init__(meta)
		self.varname = varname
		self.value = value


class Include(_Modifier):
	"""
	Represents an Include Opcode. Created by Lark transformer when importing SFZ.
	"""

	def __init__(self, filename, meta):
		super().__init__(meta)
		self.filename = filename


# ---------------------------
# Validators

class _Validator:

	def type_name(self):
		return "any" if self.type is None else self.type.__name__


class AnyValidator(_Validator):

	def is_valid(self, *_):
		return True


class ChoiceValidator(_Validator):

	@classmethod
	def from_rule(cls, str_choices, type_):
		return ChoiceValidator(
			[ c.strip("' []") for c in str_choices.split(',') ],
			type_)

	def __init__(self, choices, type_):
		self.choices = choices
		self.type = type_

	def is_valid(self, value, validate_type = True):
		if validate_type and not isinstance(value, self.type):
			return False
		return value in self.choices


class RangeValidator(_Validator):

	@classmethod
	def from_rule(cls, rulestr, type_):
		lo, hi = rulestr.split(',')
		if type_ is None:
			type_ = int
		return RangeValidator(type_(lo), type_(hi), type_)

	def __init__(self, lowval, highval, type_):
		self.lowval = lowval
		self.highval = highval
		self.type = type_

	def is_valid(self, value, validate_type = True):
		if validate_type and not isinstance(value, self.type):
			return False
		return self.lowval <= value <= self.highval


class MinValidator(_Validator):

	@classmethod
	def from_rule(cls, rulestr, type_):
		if type_ is None:
			type_ = int
		return MinValidator(type_(rulestr), type_)

	def __init__(self, lowval, type_):
		self.lowval = lowval
		self.type = type_

	def is_valid(self, value, validate_type = True):
		if validate_type and not isinstance(value, self.type):
			return False
		return self.lowval <= value


@cache
def validator_for(opcode_name):
	"""
	Returns a class which extends _Validator
	"""
	rule = validation_rule(opcode_name)
	if rule is None:
		return AnyValidator()
	match = re.match(r'^(Choice|Range|Min|Any)\(([^\)]*)\)', rule)
	if match is None:
		raise RuntimeError('Invalid validation rule: ' + rule)
	type_ = data_type(opcode_name)
	if match.group(1) == 'Choice':
		return ChoiceValidator.from_rule(match.group(2), type_)
	if match.group(1) == 'Range':
		return RangeValidator.from_rule(match.group(2), type_)
	if match.group(1) == 'Min':
		return MinValidator.from_rule(match.group(2), type_)
	return AnyValidator()

@cache
def validation_rule(opcode_name):
	definition = opcode_definition(opcode_name)
	if definition is None:
		return None
	try:
		rule = definition["value"]["valid"]
	except KeyError:
		return validation_rule(definition["modulates"]) \
			if "modulates" in definition else None
	match = re.match(r'^(Any|Alias|Choice|Range|Min)\(([^\)]*)\)', rule)
	if match is None:
		raise RuntimeError('Invalid validation rule: ' + rule)
	return validation_rule(match.group(2).strip("'")) \
		if match.group(1) == 'Alias' \
		else match.group(0)

@cache
def data_type(opcode_name):
	"""
	Normalizes an opcode_name and returns the data type.
	"""
	definition = opcode_definition(opcode_name)
	if definition is None:
		return None
	if "value" not in definition or "type" not in definition["value"]:
		return data_type(definition["modulates"]) \
			if "modulates" in definition else None
	if definition["value"]["type"] == 'float':
		return float
	if definition["value"]["type"] == 'integer':
		return int
	if definition["value"]["type"] == 'string':
		return str
	raise Exception("unknown type: " + definition["value"]["type"])

@cache
def modulates(opcode_name):
	"""
	Returns the name of the opcode that the given opcode modulates, if applicable.
	"""
	definition = opcode_definition(opcode_name)
	try:
		return definition["modulates"]
	except KeyError:
		return None

@cache
def opcode_definition(opcode_name):
	"""
	Normalizes an opcode_name and returns the matching opcode definition.
	"""
	opcode_name = normal_opcode(opcode_name)
	return None if opcode_name is None else OPCODES[opcode_name]

@cache
def normal_opcode(opcode_name, follow_aliases = True):
	"""
	Normalizes a "_ccN" opcode opcode_name.
	If "follow_aliases" is True, returns the name of the opcode that this opcode aliases.
	"""
	if opcode_name is None:
		logging.warning('opcode_name is None')
		return None
	if opcode_name in OPCODES:
		return aliases(opcode_name) if follow_aliases else opcode_name
	if re.match(r'amp_velcurve_(\d+)', opcode_name):
		return 'amp_velcurve_N'
	if re.search(r'eq\d+_', opcode_name):
		opcode_name = re.sub(r'eq\d+_', 'eqN_', opcode_name)
		if opcode_name in OPCODES:
			return aliases(opcode_name) if follow_aliases else opcode_name
		if re.search(r'cc\d', opcode_name):
			for regex, repl in [
				(r'_oncc(\d+)', '_onccX'),
				(r'_cc(\d+)', '_ccX'),
				(r'cc(\d+)', 'ccX')
			]:
				sub = re.sub(regex, repl, opcode_name)
				if sub != opcode_name and sub in OPCODES:
					return aliases(sub) if follow_aliases else opcode_name
	if re.search(r'cc\d', opcode_name):
		for regex, repl in [
			(r'_oncc(\d+)', '_onccN'),
			(r'_cc(\d+)', '_ccN'),
			(r'cc(\d+)', 'ccN')
		]:
			sub = re.sub(regex, repl, opcode_name)
			if sub != opcode_name:
				# Recurse for opcodes like "eq3_gain_oncc12"
				if sub in OPCODES:
					return aliases(sub) if follow_aliases else opcode_name
				logging.debug('normal_opcode: Falling through to do recursive checking')
				return normal_opcode(sub, follow_aliases)
	return None

@cache
def aliases(opcode_name, only_alias = False):
	"""
	Returns the opcode which the given opcode aliases, (if it does).
	If it is not aliasing another opcode, the return value depends upon the
	"only_alias" argument. When "only_alias" is True, and the given opcode does not
	alias another opcode, returns None. When "only_alias" is False (the default),
	and the given opcode does not alias another opcode, returns the given opcode.
	"""
	definition = OPCODES[opcode_name]
	if definition is not None:
		try:
			match = re.match(r'Alias\([\'"](\w+)[\'"]\)', definition['value']['valid'])
		except KeyError:
			pass
		else:
			if match:
				return match.group(1)
	return None if only_alias else opcode_name


#  end sfzen/sfz_elems.py
