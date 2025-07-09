#  sfzen/sort.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Provides functions used for sorting opcodes in a preferred order.
"""

OPCODE_SORT_ORDER = [
	'lokey',
	'hikey',
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

def midi_key_sort(region):
	"""
	Provides a key to use for sorting a list of Regions based on "lokey", "hikey" values.
	"""
	opcodes = region.inherited_opcodes()
	key = region.opcode('key')
	if key is None:
		lokey = region.opcode('lokey').value or 1
		hikey = region.opcode('hikey').value or 127
	else:
		lokey = key.value
		hikey = key.value
	return lokey * 128 + hikey


#  end sfzen/sort.py
