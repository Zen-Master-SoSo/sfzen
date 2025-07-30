#  sfzen/sort.py
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
Provides functions used for sorting opcodes in a preferred order.
"""

OPCODE_SORT_ORDER = [
	'lokey',
	'hikey',
	'pitch_keycenter',
	'lovel',
	'hivel',
	'lochan',
	'hichan',
	'sample',
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

def opcode_sorted(opcodes):
	"""
	Sort a list of Opcode objects according to preferred OPCODE_SORT_ORDER.
	"""
	return sorted(opcodes, key = lambda opcode: \
		OPCODE_SORT_ORDER.index(opcode.name) \
		if opcode.name in OPCODE_SORT_ORDER else 1000)

def name_sorted(opcodes):
	"""
	Sort a list of strings (opcode names), according to preferred OPCODE_SORT_ORDER.
	"""
	return sorted(opcodes, key = lambda opcode: \
		OPCODE_SORT_ORDER.index(opcode) \
		if opcode in OPCODE_SORT_ORDER else 1000)

def opstring_sorted(opstrings):
	def sort_val(opstring):
		op = opstring.split('=', 1)[0]
		return OPCODE_SORT_ORDER.index(op) \
		if op in OPCODE_SORT_ORDER else 1000
	return sorted(opstrings, key = sort_val)

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


#  end sfzen/sort.py
