#  sfzen/sfzen/utils/sample_unit_opcodes.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  sfzen/utils/sample_unit_opcodes.py
#
#  Copyright 2025 liyang <liyang@veronica>
#
"""
Compile a list of opcodes which use "sample units"
"""
from pretty_repr import Repr
from sfzen.opcodes import OPCODES
from sfzen.sfz_elems import aliases, modulates

SAMPLE_UNIT_OPCODES = []
for opcode in OPCODES.values():
	try:
		unit = opcode['value']['unit']
	except KeyError:
		continue
	if unit == 'sample units':
		SAMPLE_UNIT_OPCODES.append(opcode['name'])

for opcode in OPCODES.values():
	alias = aliases(opcode['name'], True)
	if alias in SAMPLE_UNIT_OPCODES:
		SAMPLE_UNIT_OPCODES.append(opcode['name'])

for opcode in OPCODES.values():
	mod = modulates(opcode['name'])
	if mod and mod in SAMPLE_UNIT_OPCODES:
		SAMPLE_UNIT_OPCODES.append(opcode['name'])

SAMPLE_UNIT_OPCODES = list(set(SAMPLE_UNIT_OPCODES))
SAMPLE_UNIT_OPCODES.sort()
Repr(SAMPLE_UNIT_OPCODES).print()

#  end sfzen/utils/sample_unit_opcodes.py
