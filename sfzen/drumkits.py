#  sfzen/sfzen/drumkits.py
#
#  Copyright 2025-2026 Leon Dionne <ldionne@dridesign.sh.cn>
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
Provides classes which are used to manipulate SFZ files in a structure
correlating with MIDI drum categories and naming conventions.
"""
import logging
from os import linesep
from os.path import dirname
from functools import reduce
from operator import and_, or_
from midi_notes import Note, MIDI_DRUM_IDS, MIDI_DRUM_PITCHES, MIDI_DRUM_NAMES
from sfzen import (
	KEY_DEFINING_OPCODES,
	opstrings_to_dict, opcodes_to_opstrings, sorted_opstrings, sorted_opcode_names,
	SFZ, Header, Group, Region)


# -----------------------------------------------------------------
# constants

COMMENT_DIVIDER = '// ' + '-' * 59 + linesep

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

LOKEY_HIKEY_OPCODES = [ 'lokey', 'hikey' ]


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

class PercussionInstrument:
	"""
	Reresents a single instrument trigerred by a single MIDI note number.
	When importing from an SFZ, this class contains the regions that define the
	sound of the instrument.
	"""

	source_filename = None

	def __init__(self, pitch):
		"""
		pitch:		(int)	MIDI note number
		"""
		self.note = Note(pitch)
		self.pitch = self.note.pitch
		self.inst_id = MIDI_DRUM_IDS[pitch]
		self.name = MIDI_DRUM_NAMES[pitch]
		self.elements = []

	def samples(self):
		"""
		Generator which yields all the samples used by this PercussionInstrument
		"""
		for element in self.elements:
			yield from element.samples()

	def is_empty(self):
		"""
		Returns True if there are no regions defined for this Instrument's pitch
		"""
		return len(self.elements) == 0

	def kitwalk(self, depth = 0):
		"""
		Generator which recusively yields every element contained in this
		PercussionInstrument. Each iteration returns a tuple (Element, (int) depth)
		"""
		yield (self, depth)
		depth += 1
		for element in self.elements:
			yield from element.walk(depth)

	def clone(self):
		inst = PercussionInstrument(self.pitch)
		inst.elements = [ element.clone() for element in self.elements ]
		inst.source_filename = self.source_filename
		return inst

	def write(self, stream):
		"""
		Write in SFZ format to any file-like object, including sys.stdout
		"global_opstrings" is a set of string representations (including name and
		value) of all the opcodes NOT to define, as they are common opcodes defined in
		a parent header.
		"""
		stream.write(f'//  "{self.name}" - key {self.pitch} "{self.note}"{linesep}{linesep}')
		if self.source_filename:
			stream.write(f'// Source: {self.source_filename}{linesep}')
		for element in self.elements:
			element.write(stream)
		stream.write(linesep)

	def __repr__(self):
		return f'<PercussionInstrument "{self.name}" (key {self.pitch} - {self.note})>'


class PercussionGroup:
	"""
	Class used for organizing instruments in a Drumkit, not to be confused with a
	<group> header in an SFZ file.
	Allows for the manipulation of an entire category of instruments.
	"""

	source_filename = None

	def __init__(self, group_id):
		self.group_id = group_id
		self.name = group_id.replace('_', ' ').title()
		self.instruments = { }	# { pitch : PercussionInstrument }

	def append_instrument(self, pitch):
		"""
		Adds or replaces an instrument in this group.
		pitch:	(int)	MIDI note number
		"""
		self.instruments[pitch] = PercussionInstrument(pitch)
		return self.instruments[pitch]

	def is_empty(self):
		"""
		Returns True if not containing any instruments, or contained instruments
		contain no Region -type headers.
		"""
		return all(inst.is_empty() for inst in self.instruments.values())

	def samples(self):
		"""
		Generator which yields every sample opcode (Opcode class)
		"""
		for instrument in self.instruments.values():
			yield from instrument.samples()

	def kitwalk(self, depth = 0):
		"""
		Generator which recusively yields every element contained in this Drumkit,
		Each iteration returns a tuple (Element, (int) depth)
		"""
		yield (self, depth)
		depth += 1
		for instrument in self.instruments.values():
			yield from instrument.kitwalk(depth)

	def clone(self):
		group = PercussionGroup(self.group_id)
		group.instruments = { pitch : instrument.clone()
			for pitch, instrument in self.instruments.items() }
		return group

	def write(self, stream):
		"""
		Write in SFZ format to any file-like object, including sys.stdout
		"""
		stream.write(f'{COMMENT_DIVIDER}// Percussion Group "{self.name}"' +
			f'{linesep}{COMMENT_DIVIDER}{linesep}')
		for inst in self.instruments.values():
			if not inst.is_empty():
				inst.write(stream)
		stream.write(linesep)

	def __repr__(self):
		return f"<PercussionGroup {self.name}>"


class Drumkit(SFZ):
	"""
	A special structure for an SFZ which organizes percussion instruments by groups.
	Passing a filename to the constructor loads the given .sfz file and attaches
	its regions to a PercussionInstrument. These are organized under
	PercussionGroup objects.
	You may instantiate an empty Drumkit object and import instruments or groups of
	instruments from other Drumkit objects.
	Writing a Drumkit produces a standard SFZ formatted text file. The only
	evidence of the grouping of Regions under PercussionInstrument /
	PercussionGroup appear in the comments.
	"""

	def __init__(self, filename = None):
		self.percussion_groups = { }
		self.elements = []
		self._opcodes = {}
		if filename:
			self.path = filename
			self._parse()

	def _parse(self):
		sfz = SFZ(self.path)
		for sample in sfz.samples():
			sample.value = sample.abspath
		for pitch, group_id in PITCH_GROUPS.items():
			region_opstring_sets = [ opcodes_to_opstrings(region.inherited_opcodes().values())
				for region in sfz.regions_for(key = pitch) ]
			if region_opstring_sets:
				instrument = self.percussion_group(group_id).append_instrument(pitch)

				if len(region_opstring_sets) > 1:
					group = Group()
					common_dict = opstrings_to_dict(reduce(and_, region_opstring_sets))
					for name in LOKEY_HIKEY_OPCODES:
						if name in common_dict:
							del common_dict[name]
					common_dict['key'] = pitch
					for name in sorted_opcode_names(list(common_dict.keys())):
						group.append_opcode(name, common_dict[name])
				else:
					group = None
					common_dict = set()

				for opstrings in region_opstring_sets:
					region = Region()
					region_dict = opstrings_to_dict(opstrings)
					for name in LOKEY_HIKEY_OPCODES:
						if name in region_dict:
							del region_dict[name]
					if common_dict:
						if 'key' in region_dict:
							del region_dict['key']
						for name in sorted_opcode_names(list(region_dict.keys())):
							if name not in common_dict:
								region.append_opcode(name, region_dict[name])
						group.append(region)
					else:
						region_dict['key'] = pitch
						for name in sorted_opcode_names(list(region_dict.keys())):
							region.append_opcode(name, region_dict[name])
						instrument.elements.append(region)
						self.append(region)

				if common_dict:
					instrument.elements.append(group)
					self.append(group)

	def import_group(self, group):
		"""
		Clone and adopt the given (PercussionGroup) group
		"""
		self.percussion_groups[group.group_id] = group.clone()
		for instrument in self.percussion_groups[group.group_id].instruments.values():
			for element in instrument.elements:
				element.parent = self

	def import_instrument(self, instrument):
		"""
		Clone and adopt the given (PercussionInstrument) instrument
		"""
		group_id = PITCH_GROUPS[instrument.pitch]
		my_group = self.percussion_group(group_id)
		my_group.instruments[instrument.pitch] = instrument.clone()
		for element in my_group.instruments[instrument.pitch].elements:
			element.parent = self

	def delete_instrument(self, pitch_or_id):
		"""
		Removes an instrument.
		"""
		pitch, _ = pitch_id_tuple(pitch_or_id)
		group_id = PITCH_GROUPS[pitch]
		del self.percussion_groups[group_id].instruments[pitch]

	def regions(self):
		"""
		Generator which yields every Region header
		"""
		for group in self.percussion_groups.values():
			yield from group.regions()

	def samples(self):
		"""
		Generator which yields every sample opcode (Opcode class)
		"""
		for group in self.percussion_groups.values():
			yield from group.samples()

	def instruments(self):
		"""
		Generator function which yields every instrument.
		"""
		for group in self.percussion_groups.values():
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
		return self.percussion_groups[group_id].instruments[pitch]

	def percussion_group(self, group_id):
		"""
		Returns PercussionGroup
		Creates empty group if it doesn't exist
		"""
		if not group_id in self.percussion_groups:
			self.percussion_groups[group_id] = PercussionGroup(group_id)
		return self.percussion_groups[group_id]

	def kitwalk(self, depth = 0):
		"""
		Generator which recusively yields every element contained in this Drumkit,
		ordered by PercussionGroup -> PercussionInstrument -> Region -> Opcode.
		Each iteration returns a tuple (Element, (int) depth)
		"""
		yield (self, depth)
		depth += 1
		for group in self.percussion_groups.values():
			yield from group.kitwalk(depth)

	def kitdump(self):
		"""
		Print (to stdout) a concise outline of this SFZ.
		"""
		for elem, depth in self.kitwalk():
			print('  ' * depth + repr(elem))

	def write(self, stream):
		"""
		Write in SFZ format to any file-like object, including sys.stdout.
		"""
		stream.write(f'//{linesep}// {self.filename}{linesep}//{linesep}')
		for group in self.percussion_groups.values():
			if not group.is_empty():
				group.write(stream)

	def __repr__(self):
		return f"<Drumkit>"


#  end sfzen/sfzen/drumkits.py
