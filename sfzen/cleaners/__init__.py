#  sfzen/sfzen/cleaners/__init__.py
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
"""
Cleaners subpackage of the sfzen package.

Provides functions supportive of removing opcodes from SFZs which are not
supported by your favorite player.
"""
from sfzen import normal_opcode

def filter_opcodes(sfz, supported_opcodes):
	for elem, _ in sfz.reverse_header_walk():
		removals = [ name for name in elem.opcodes().keys() \
			if not normal_opcode(name) in supported_opcodes ]
		elem.remove_opcodes(removals)
