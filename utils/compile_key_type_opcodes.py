#  sfzen/utils/compile_key_type_opcodes.py
#
#  Copyright 2026 Leon Dionne <ldionne@dridesign.sh.cn>
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
from repr_soso import Repr
from sfzen import OPCODES, K_VALUE, K_MIN, K_MAX, K_NAME

names = []
for opcode_def in OPCODES.values():
	if K_VALUE in opcode_def:
		if opcode_def[K_VALUE][K_MIN] == 0 \
			and opcode_def[K_VALUE][K_MAX] == 127 \
			and 'lovel' not in opcode_def[K_NAME] \
			and 'hivel' not in opcode_def[K_NAME] \
			and 'prog' not in opcode_def[K_NAME] \
			and 'polyaft' not in opcode_def[K_NAME] \
			and 'sostenuto' not in opcode_def[K_NAME] \
			and 'sustain' not in opcode_def[K_NAME] \
			and 'cc' not in opcode_def[K_NAME] \
			and 'chan' not in opcode_def[K_NAME]:
			names.append(opcode_def[K_NAME])

Repr(names).print()
print()


#  end sfzen/utils/compile_key_type_opcodes.py
