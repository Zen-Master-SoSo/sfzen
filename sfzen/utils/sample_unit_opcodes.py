#  sfzen/utils/sample_unit_opcodes.py
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
