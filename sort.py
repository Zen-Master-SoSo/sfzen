#  sfzen/sort.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
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
	return sorted(opcodes, key = lambda opcode: \
		OPCODE_SORT_ORDER.index(opcode.name) \
		if opcode.name in OPCODE_SORT_ORDER else 1000)

def name_sorted(opstrings):
	return sorted(opstrings, key = lambda opstring: \
		OPCODE_SORT_ORDER.index(opstring) \
		if opstring in OPCODE_SORT_ORDER else 1000)


#  end sfzen/sort.py
