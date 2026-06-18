# pylint: disable = duplicate-code
#
#  sfzen/scripts/sfz_opcode_info.py
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
Displays data type, allowable values, aliases and descriptions of opcodes.
"""
import sys, logging, argparse
from os import linesep
from textwrap import wrap
from sfzen import (
	LOG_FORMAT,
	opcode_definition,
	K_CATEGORY,
	K_NAME,
	K_VERSION,
	K_DESCRIPTION,
	K_MODULATES,
	K_VALUE,
	K_VAR_TYPE,
	K_UNIT,
	K_DEFAULT,
	K_MIN,
	K_MAX,
	K_CHOICES
)
from sfzen.opcodes import CATEGORIES

KEYLEN = 13

def main():
	"""
	Entry point for importing script from elsewhere.
	TODO: Return value
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('Opcode', type = str, nargs = '+',
		help = 'Opcode to inspect.')
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information.')
	parser.epilog = __doc__
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = LOG_FORMAT
	)

	def _ver(c):
		return ' ' * 6 if c[K_VERSION] is None \
			else f'({c[K_VERSION]})'.ljust(6)

	for opcode_name in options.Opcode:	# pylint: disable = too-many-nested-blocks
		print(opcode_name)
		print('-' * len(opcode_name))
		d = opcode_definition(opcode_name)
		if d is None:
			print('Nothing found!')
		else:
			print('Opcode name:'.ljust(KEYLEN) + d[K_NAME])
			print('Category:'.ljust(KEYLEN) + CATEGORIES[d[K_CATEGORY]][K_NAME])
			if d[K_VERSION]:
				print('Version:'.ljust(KEYLEN) + d[K_VERSION])
			if d[K_MODULATES]:
				print('Modulates:'.ljust(KEYLEN) + d[K_MODULATES])
			if v := d[K_VALUE]:
				if v[K_VAR_TYPE]:
					print('Type:'.ljust(KEYLEN) + v[K_VAR_TYPE])
				if v[K_UNIT]:
					print('Unit:'.ljust(KEYLEN) + v[K_UNIT])
				if v[K_CHOICES]:
					print('Choices:')
					namelen = max(len(c[K_NAME]) for c in v[K_CHOICES])
					for c in v[K_CHOICES]:
						print(f' {_ver(c)} {c[K_NAME].ljust(namelen)}', end = '')
						if c[K_DESCRIPTION]:
							desc = wrap(c[K_DESCRIPTION])
							print(' ' + desc.pop(0))
							if desc:
								spc = ' ' * (namelen + 9)
								print(spc + f'{linesep}{spc}'.join(desc))
						else:
							print()
				if v[K_MIN] is not None:
					print('Min:'.ljust(KEYLEN) + str(v[K_MIN]))
				if v[K_MAX] is not None:
					print('Max:'.ljust(KEYLEN) + str(v[K_MAX]))
				if v[K_DEFAULT]:
					print('Default:'.ljust(KEYLEN) + v[K_DEFAULT])
			if d[K_DESCRIPTION]:
				print(f'Description:{linesep}   ', end = '')
				print(f'{linesep}   '.join(wrap(d[K_DESCRIPTION])))
		print()


if __name__ == '__main__':
	sys.exit(main() or 0)


#  end sfzen/scripts/sfz_opcode_info.py
