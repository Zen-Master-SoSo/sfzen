#  sfzen/sfz_elems.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Classes which are instantiated when parsing an .sfz file.
All of these classes are constructed from a lark parser tree Token.
"""
import os, logging, re
from functools import cached_property
from functools import reduce
from operator import or_
from appdirs import user_cache_dir
from lark import Lark, Transformer, v_args
from sfzen.opcodes import OPCODES


class _SFZElem:

	_ordinals = {}

	def __init__(self, meta):
		typ = type(self).__name__
		if typ not in _SFZElem._ordinals:
			_SFZElem._ordinals[typ] = 1
		self._idx = _SFZElem._ordinals[typ]
		_SFZElem._ordinals[typ] += 1
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

	def sfz(self):
		"""
		Returns the parent SFZ which contains this element.
		"""
		elem = self
		while not isinstance(elem, SFZ):
			elem = elem.parent
		return elem


class _Header(_SFZElem):
	"""
	The _Header class is an abstract class which handles the functions common to
	all SFZ header types. Each header type basically acts the same, except for
	checking what kind of subheader it may contain.
	"""

	def __init__(self, toks, meta):
		super().__init__(meta)
		self._subheadings = []
		self._opcodes = {}

	def may_contain(self, header):
		"""
		This function is used to determine if a header being parsed is a child of the
		last previous header, or the start of an entirely new header group.
		"""
		return False

	def append_opcode(self, opcode):
		"""
		Function used during parsing.
		"""
		self._opcodes[opcode.name] = opcode
		opcode.parent = self

	def append_subheader(self, subheading):
		"""
		Function used during parsing.
		"""
		self._subheadings.append(subheading)
		subheading.parent = self

	def inherited_opcodes(self):
		"""
		Returns all the opcodes defined in this header with all opcodes defined in its
		parent header, recursively. Opcodes defined in this header override parent's.
		"""
		return dict(self._parent.inherited_opcodes(), **self._opcodes)

	def regions(self):
		"""
		Returns all <region> headers contained by this header and all of its child
		headers.
		"""
		for sub in self._subheadings:
			if isinstance(sub, Region):
				yield sub
			yield from sub.regions()

	def opcode(self, name):
		"""
		Returns an Opcode with the given name, if one exists in this header or any of
		its ancestors. Returns None if no such opcode exists.
		"""
		return self._opcodes[name] if name in self._opcodes \
			else None if self._parent is None \
			else self._parent.opcode(name)

	def opcodes_used(self):
		"""
		Returns a set of the keys of all the opcodes used in this _Header.
		"""
		mine = set(self._opcodes.keys())
		return mine | reduce(or_, [heading.opcodes_used() for heading in self._subheadings]) \
			if self._subheadings \
			else mine

	@property
	def opcodes(self):
		"""
		Returns a dictionary of Opcode ojects, whose keys are the Opcode's name.
		"""
		return self._opcodes

	@property
	def subheadings(self):
		"""
		Returns a list of headers contained in this header.
		"""
		return self._subheadings

	def __repr__(self):
		return '%-4d| %s #%s (%d opcodes)' % (self.line, type(self).__name__, self._idx, len(self._opcodes))

	def __str__(self):
		return '<%s>' % type(self).__name__.lower()

	def write(self, stream):
		"""
		Exports this header and all of it's contained headers and
		opcodes to .sfz format.
		"stream" may be any file-like object, including sys.stdout.
		"""
		stream.write(str(self) + "\n")
		opcodes = self._opcodes.values()
		if opcodes:
			for op in self._opcodes.values():
				op.write(stream)
			stream.write("\n")
		if self._subheadings:
			for sub in self._subheadings:
				sub.write(stream)


class _Modifier(_SFZElem):
	pass


class Global(_Header):

	def may_contain(self, header):
		return True


class Master(_Header):

	def may_contain(self, header):
		return type(header) not in [Global, Master]


class Group(_Header):

	def may_contain(self, header):
		return type(header) not in [Global, Master, Group]


class Region(_Header):

	def may_contain(self, header):
		return type(header) not in [Global, Master, Group, Region]

	def is_triggerd_by(self, lokey=None, hikey=None, lovel=None, hivel=None):
		"""
		Returns boolean True/False if this Region matches the given criteria.
		For example, to test if this region plays Middle C at any velocity:
			region.is_triggerd_by(lokey = 60, hikey = 60)
		"""
		if lokey is None and hikey is None and lovel is None and hivel is None:
			raise Exception('Requires a key or velocity to test')
		ops = self.inherited_opcodes()
		if 'lokey' in ops and lokey is not None and ops['lokey'].value > lokey:
			return False
		if 'hikey' in ops and hikey is not None and ops['hikey'].value < hikey:
			return False
		if 'lovel' in ops and lovel is not None and ops['lovel'].value > lovel:
			return False
		if 'hivel' in ops and hivel is not None and ops['hivel'].value < hivel:
			return False
		return True

	@cached_property
	def opstrs(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes which are used by this Region.
		Note that when a Drumkit Region is imported from an SFZ or another Drumkit,
		opcodes from the source region as well as opcodes inherited from container
		groups, (such as "Group", "Master", and "Global" groups), are included.
		"""
		return set(str(opcode) for opcode in self._opcodes.values())

	def uses_opstr(self, opstr):
		"""
		Returns True if the given string representation (including name and value) of
		an opcode is used by this Region. Checks opcodes defined in this Region as well
		as opcodes inherited from container groups, such as Group, Master, and Global
		groups.
		Note that opcode name AND value must match.
		"""
		return opstr in self.opstrs

	@property
	def sample(self):
		"""
		Returns the parsed value of the "sample" opcode contained in this region, if
		one exists.
		"""
		return self.opcodes['sample']._parsed_value if 'sample' in self.opcodes else None


class Control(_Header):
	pass


class Effect(_Header):
	pass


class Midi(_Header):
	pass


class Curve(_Header):

	curve_index = None
	points = {}

	def __repr__(self):
		return '%-4d| %s #%s curve_index %s (%d points)' % \
			(self.line, type(self).__name__, self._idx, self.curve_index, len(self.points))

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


class Opcode(_SFZElem):

	def __init__(self, name, value, meta):
		super().__init__(meta)
		self.name = name
		self._parsed_value = value

	@cached_property
	def value(self):
		"""
		Returns the value as the type defined in the opcode definition.
		"""
		if self.type == 'float':
			return float(self._parsed_value)
		elif self.type == 'integer':
			return int(self._parsed_value)
		return self._parsed_value

	@cached_property
	def type(self):
		"""
		Returns the type defined in the opcode definition.
		"""
		return self._def_value('type')

	@cached_property
	def unit(self):
		"""
		Returns the unit defined in the opcode definition.
		"""
		return self._def_value('unit')

	@cached_property
	def valid(self):
		"""
		Returns the validation rule defined in the opcode definition.
		"""
		return self._def_value('valid')

	@cached_property
	def definition(self):
		"""
		Returns the defintion of this opcode from the SFZ syntax (see opcodes.py)
		The defintion name is normalized, replacing "_ccN" -type elements.
		"""
		return OPCODES[self.name] \
			if self.name in OPCODES \
			else self._get_opcode_def(self.name)

	def _def_value(self, key):
		"""
		Returns the attribute of the opcode defintion.value, if defined,
		returns None if not.
		"""
		return None \
			if self.definition is None or 'value' not in self.definition \
			else self.definition['value'][key]

	def _get_opcode_def(self, name):
		"""
		Normalizes a "_ccN" opcode name and returns the matching opcode definition.
		"""
		if re.match(r'amp_velcurve_(\d+)', name):
			return 'amp_velcurve_N'
		if re.search(r'eq\d+_', name):
			name = re.sub(r'eq\d+_', 'eqN_', name)
			if name in OPCODES:
				return OPCODES[name]
			if re.search(r'cc\d', name):
				for regex, repl in {
					r'_oncc(\d+)'	: '_onccX',
					r'_cc(\d+)'		: '_ccX',
					r'cc(\d+)'		: 'ccX'
				}.items():
					sub = re.sub(regex, repl, name)
					if sub != name and sub in OPCODES:
						return OPCODES[sub]
		if re.search(r'cc\d', name):
			for regex, repl in {
				r'_oncc(\d+)'	: '_onccN',
				r'_cc(\d+)'		: '_ccN',
				r'cc(\d+)'		: 'ccN'
			}.items():
				sub = re.sub(regex, repl, name)
				if sub != name:
					# Recurse for opcodes like "eq3_gain_oncc12"
					return OPCODES[sub] if sub in OPCODES else self._get_opcode_def(sub)
		logging.warning('Could not find opcode ' + name)

	def __repr__(self):
		return '%-4d| opcode #%d: "%s" = %s' % (self.line, self._idx, self.name, repr(self.value))

	def __str__(self):
		return '%s=%s' % (self.name, self._parsed_value)

	def write(self, stream):
		"""
		Exports this Opcode to .sfz format.
		"stream" may be any file-like object, including sys.stdout.
		"""
		stream.write(str(self) + "\n")


class Define(_Modifier):

	def __init__(self, varname, value, meta):
		super().__init__(meta)
		self.varname = varname
		self.value = value

	def __repr__(self):
		return '%-4d| define #%d: %s = %s' % (self.line, self._idx, self.varname, self.value)


class Include(_Modifier):

	def __init__(self, path, meta):
		super().__init__(meta)
		self.path = path

	def __repr__(self):
		return '%-4d| include #%d: %s' % (self.line, self._idx, self.path)


#  end sfzen/sfz_elems.py
