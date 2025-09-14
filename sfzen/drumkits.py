#  sfzen/drumkits.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
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
Provides Drumkit SFZ wrapper which allows import / copy operations.
"""
from os.path import basename
from copy import deepcopy
from functools import reduce
from operator import and_, or_
from midi_notes import Note, MIDI_DRUM_IDS, MIDI_DRUM_PITCHES, MIDI_DRUM_NAMES
from sfzen import COMMENT_DIVIDER, SFZ, KEY_OPCODES
from sfzen.sort import opstring_sorted
from sfzen.sfz_elems import Region as SFZRegion

# -----------------------------------------------------------------
# constants

GROUP_PITCHES = {
	'bass_drums'	: [35, 36],
	'snares'		: [37, 38, 39, 40],
	'tom_toms'		: [41, 43, 45, 47, 48, 50],
	'high_hats'		: [42, 44, 46],
	'crashes'		: [49, 57],
	'rides'			: [51, 53, 59],
	'other_cymbals'	: [52, 55, 56],
	'bongos'		: [60, 61],
	'congas'		: [62, 63, 64],
	'agogos'		: [67, 68],
	'timbales'		: [65, 66],
	'guiros'		: [73, 74],
	'woodblocks'	: [76, 77],
	'triangles'		: [80, 81],
	'cuica'			: [78, 79],
	'whistle'		: [71, 72],
	'others'		: [54, 58, 69, 70, 75]
}

PITCH_GROUPS = {
	35	: 'bass_drums',
	36	: 'bass_drums',
	37	: 'snares',
	38	: 'snares',
	39	: 'snares',
	40	: 'snares',
	41	: 'tom_toms',
	43	: 'tom_toms',
	45	: 'tom_toms',
	47	: 'tom_toms',
	48	: 'tom_toms',
	50	: 'tom_toms',
	42	: 'high_hats',
	44	: 'high_hats',
	46	: 'high_hats',
	49	: 'crashes',
	57	: 'crashes',
	51	: 'rides',
	53	: 'rides',
	59	: 'rides',
	52	: 'other_cymbals',
	55	: 'other_cymbals',
	56	: 'other_cymbals',
	60	: 'bongos',
	61	: 'bongos',
	62	: 'congas',
	63	: 'congas',
	64	: 'congas',
	67	: 'agogos',
	68	: 'agogos',
	65	: 'timbales',
	66	: 'timbales',
	73	: 'guiros',
	74	: 'guiros',
	76	: 'woodblocks',
	77	: 'woodblocks',
	80	: 'triangles',
	81	: 'triangles',
	78	: 'cuica',
	79	: 'cuica',
	71	: 'whistle',
	72	: 'whistle',
	54	: 'others',
	58	: 'others',
	69	: 'others',
	70	: 'others',
	75	: 'others'
}


# -----------------------------------------------------------------
# funcs

def iter_pitch_by_group():
	for pitches in GROUP_PITCHES.values():
		yield from pitches

def pitch_id_tuple(pitch_or_id):
	"""
	Returns tuple:
		(int) pitch
		(str) instrument_id
	"pitch_or_id" may be a pitch or an instrument id string (i.e. "side_stick").
	"""
	if pitch_or_id in MIDI_DRUM_IDS:
		return pitch_or_id, MIDI_DRUM_IDS[pitch_or_id]
	if pitch_or_id in MIDI_DRUM_PITCHES:
		return MIDI_DRUM_PITCHES[pitch_or_id], pitch_or_id
	raise ValueError(f'"{pitch_or_id}" not recognized as an instrument id or pitch' )


# -----------------------------------------------------------------
# Drumkit classes

class Region(SFZRegion):
	"""
	A representation of an SFZ <region> header.

	Note that when a Drumkit Region is imported from an SFZ or another Drumkit,
	opcodes from the source region as well as opcodes inherited from container
	groups, (such as "Group", "Master", and "Global" groups), are included.

	"""

	def __init__(self, source_region, source_filename):
		self._parent = None
		self._subheaders = []
		self._opcodes = source_region.inherited_opcodes()
		self.filename = source_filename
		self.line = source_region.line
		self.column = source_region.column
		self.end_line = source_region.end_line
		self.end_column = source_region.end_column

	def write(self, stream, region_exclude):
		"""
		Write in SFZ format to any file-like object, including sys.stdout.

		"region_exclude" is a set of string representations (including name and value)
		of all the opcodes NOT to define in this region, as they are common opcodes
		defined in a parent header.
		"""
		stream.write("<region>\n")
		for opstring in opstring_sorted(self.opstrings() - region_exclude):
			stream.write(opstring + '\n')
		stream.write('\n')


class PercussionInstrument:
	"""
	Reresents a single instrument trigerred by a single MIDI note number.
	When importing from an SFZ, this class contains the regions that define the
	sound of the instrument.
	"""

	def __init__(self, pitch, regions, filename):
		"""
		Used when importing from an SFZ
		pitch:		(int)	MIDI note number
		regions:	(list)	Region headers from source SFZ
		filename:	(str)	Filename from source SFZ
		"""
		self.note = Note(pitch)
		self.pitch = self.note.pitch
		self.inst_id = MIDI_DRUM_IDS[pitch]
		self.name = MIDI_DRUM_NAMES[pitch]
		self.regions = [ Region(region, filename) for region in regions ]
		self.source_filename = filename

	def empty(self):
		"""
		Returns True if there are no regions defined for this Instrument's pitch
		"""
		return len(self.regions) == 0

	def write(self, stream, global_opstrings):
		"""
		Write in SFZ format to any file-like object, including sys.stdout

		"global_opstrings" is a set of string representations (including name and
		value) of all the opcodes NOT to define, as they are common opcodes defined in
		a parent header.
		"""
		stream.write(f'// "{self.name}" - key {self.note.pitch} / {self.note}\n')
		stream.write(f'// Source: {self.source_filename}\n\n')
		if len(self.regions) > 1:
			# Multiple regions; look for common opstrings:
			group_opstrings = self.common_opstrings() - global_opstrings
		else:
			# One region; select only key -related opstrings
			region = self.regions[0]
			group_opstrings = set(
				str(region.opcodes[key]) \
				for key in KEY_OPCODES \
				if key in region.opcodes
			)
		region_exclude = global_opstrings | group_opstrings
		# Determine if we can replace 'lokey', 'hikey' and 'pitch_keycenter with 'key':
		keyvals = [
			opstring.split('=', 1)[1] \
			for opstring in group_opstrings \
			if opstring.split('=', 1)[0] in KEY_OPCODES
		]
		if len(keyvals) == 3 and len(set(keyvals)) == 1:
			group_opstrings = [
				opstring \
				for opstring in group_opstrings \
				if opstring.split('=', 1)[0] not in KEY_OPCODES
			]
			group_opstrings.append(f'key={keyvals[0]}')
		stream.write('<group>\n')
		for opstring in opstring_sorted(group_opstrings):
			stream.write(opstring + '\n')
		stream.write('\n')
		for region in self.regions:
			region.write(stream, region_exclude)
		stream.write('\n')

	def opstrings_used(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes used in this Instrument.
		"""
		return reduce(or_, [region.opstrings() \
			for region in self.regions], set())

	def common_opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the identical opcodes used in every region in this Instrument.
		"""
		opstrings = [region.opstrings() for region in self.regions]
		return reduce(and_, opstrings) if opstrings else set()

	def samples_used(self):
		"""
		Returns a set of all raw values of all "sample" opcodes contained in the
		regions defined for this Instrument.
		"""
		return set(region.sample for region in self.regions if region.sample is not None)

	def samples(self):
		"""
		Generator which yields every sample opcode (Opcode class)
		"""
		for region in self.regions:
			if 'sample' in region.opcodes:
				yield region.opcodes['sample']


class PercussionGroup:
	"""
	Class used for organizing instruments in a Drumkit, not to be confused with a
	<group> header in an SFZ file.

	Allows for the user to select an entire category of instruments with one click
	from the gui.
	"""

	def __init__(self, group_id):
		self.group_id = group_id
		self.name = group_id.replace('_', ' ').title()
		self.instruments = { }

	def append_instrument(self, pitch, regions, filename):
		"""
		Adds or replaces an instrument in this group.
		pitch:		(int)	MIDI note number
		regions:	(list)	"region" header and contained opcodes from SFZ
		filename:	(str)	Filename from the source SFZ
		"""
		self.instruments[pitch] = PercussionInstrument(pitch, regions, filename)

	def empty(self):
		"""
		Returns True if not containing any instruments, or contained instruments
		contain no Region -type headers.
		"""
		return all(inst.empty() for inst in self.instruments.values())

	def write(self, stream, exclude_opstrings):
		"""
		Write in SFZ format to any file-like object, including sys.stdout

		"exclude_opstrings" is a set of string representations (including name and value)
		of all the opcodes NOT to define in this region, as they are common opcodes
		defined in a parent header.
		"""
		stream.write(f'{COMMENT_DIVIDER}// "{self.name}"\n{COMMENT_DIVIDER}\n')
		for inst in self.instruments.values():
			if not inst.empty():
				inst.write(stream, exclude_opstrings)

	def opstrings_used(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the opcodes used by all Instruments in this Group.
		"""
		return reduce(or_, [instrument.opstrings_used() \
			for instrument in self.instruments.values()], set())

	def common_opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the identical opcodes used in every region in this Group.
		"""
		opstrings = [instrument.opstrings_used() \
			for instrument in self.instruments.values()]
		return reduce(and_, opstrings) if opstrings else set()

	def samples_used(self):
		"""
		Returns a set of all raw values of all "sample" opcodes contained in the
		regions defined for this Instrument.
		"""
		return reduce(or_, [ instrument.samples_used() \
			for instrument in self.instruments.values() ], set())

	def samples(self):
		"""
		Generator which yields every sample opcode (Opcode class)
		"""
		for instrument in self.instruments.values():
			yield from instrument.samples()


class Drumkit(SFZ):
	"""
	A special structure for an SFZ which organizes percussion instruments by groups.

	Passing a filename to the constructor loads the given .sfz file and attaches
	its regions to a PercussionInstrument. These are organized under
	PercussionGroup objects.

	You may instantiate an empty Drumkit ohect and import instruments or groups of
	instruments from other Drumkit objects.
	"""

	def __init__(self, filename=None):
		self._parent = None
		self.groups = { group_id:PercussionGroup(group_id) for group_id in GROUP_PITCHES }
		self.filename = filename
		if self.filename is None:
			self.name = '[unnamed Drumkit]'
		else:
			sfz = SFZ(self.filename)
			for pitch, group_id in PITCH_GROUPS.items():
				regions = list(sfz.regions_for(lokey=pitch, hikey=pitch))
				if regions:
					self.groups[group_id].append_instrument(pitch, regions, filename)

	def write(self, stream):
		"""
		Write in SFZ format to any file-like object, including sys.stdout.
		"""
		stream.write(f'//\n// {self.name}\n//\n')
		global_opstrings = self.common_opstrings()
		if global_opstrings:
			stream.write('\n<global>\n')
			for opstring in opstring_sorted(global_opstrings):
				stream.write(opstring + '\n')
			stream.write('\n')
		for group in self.groups.values():
			if not group.empty():
				group.write(stream, global_opstrings)

	def import_group(self, group_id, source_kit):
		"""
		Do a deep copy from the given Drumkit, of the specified group.
		group_id:	(str)		Group ID, as from GROUP_PITCHES
		source_kit	(Drumkit)	Source to copy from

		Raises IndexError if the specified group was not found in the source kit.
		"""
		self.groups[group_id] = deepcopy(source_kit.groups[group_id])

	def import_instrument(self, pitch_or_id, source_kit):
		"""
		Do a deep copy from the given Drumkit, of the instrument tied to the spectfied
		pitch.
		pitch:		(int)		MIDI note number of the instrument to copy.
		source_kit	(Drumkit)	Source to copy from
		"""
		pitch, _ = pitch_id_tuple(pitch_or_id)
		group_id = PITCH_GROUPS[pitch]
		self.groups[group_id].instruments[pitch] = \
			deepcopy(source_kit.instrument(pitch))

	def delete_instrument(self, pitch_or_id):
		"""
		Removes an instrument - quicker than reimporting everything when changes are made.
		"""
		pitch, _ = pitch_id_tuple(pitch_or_id)
		group_id = PITCH_GROUPS[pitch]
		del self.groups[group_id].instruments[pitch]

	def common_opstrings(self):
		"""
		Returns a set of all the string representation (including name and value) of
		all the identical opcodes used in every region in this Drumkit.
		"""
		sets = [group.common_opstrings() for group in self.groups.values()]
		# Filter empty:
		sets = [ set_ for set_ in sets if len(set_) ]
		return reduce(and_, sets) if sets else set()

	def samples(self):
		"""
		Generator which yields every sample opcode (Opcode class)
		"""
		for group in self.groups.values():
			yield from group.samples()

	def samples_used(self):
		"""
		Returns a set of all raw values of all "sample" opcodes used in this Drumkit.
		"""
		return reduce(or_, [group.samples_used() \
			for group in self.groups.values()], set())

	def instruments(self):
		"""
		Generator function which yields every instrument.
		"""
		for group in self.groups.values():
			yield from group.instruments.values()

	def instrument_ids(self):
		"""
		Returns a list of (str) inst_id
		"""
		return [ instrument.inst_id for instrument in self.instruments() ]

	def instrument_pitches(self):
		"""
		Returns a list of (int) pitch
		"""
		return [ instrument.pitch for instrument in self.instruments() ]

	def instrument(self, pitch_or_id):
		"""
		Returns a PercussionInstrument.
		"pitch_or_id" may be a pitch or an instrument id string (i.e. "side_stick").

		Raises IndexError if the instrument is not found in this Drumkit.
		"""
		pitch, _ = pitch_id_tuple(pitch_or_id)
		group_id = PITCH_GROUPS[pitch]
		return self.groups[group_id].instruments[pitch]

	def group(self, group_id):
		"""
		Convenience function for syntactic uniformity.
		"""
		return self.groups[group_id]

	def __str__(self):
		return f"<Drumkit {self.name}>"


#  end sfzen/drumkits.py
