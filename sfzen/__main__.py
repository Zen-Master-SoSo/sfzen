#  sfzen/sfzen/__main__.py
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
Shows what scripts are available.
"""
import sys
from os import linesep
from os.path import join, dirname, basename, splitext
from importlib import import_module
from glob import glob
from textwrap import wrap
import sfzen
from sfzen import scripts


def _print_doc(module):
	print(module.__name__.split('.').pop().replace('_', '-'))
	print(linesep.join(wrap(module.__doc__.strip(),
		initial_indent = '  ', subsequent_indent = '  ')))
	print()

def main():
	_print_doc(sfzen)
	print('---------------------------------')
	print('Scripts included in this package:')
	print('---------------------------------')
	print()
	for filename in glob(join(dirname(scripts.__file__), '*.py')):
		module_name = splitext(basename(filename))[0]
		if module_name[0] != '_':
			_print_doc(import_module(f'.scripts.{module_name}', 'sfzen'))


if __name__ == "__main__":
	sys.exit(main())


#  end sfzen/sfzen/__main__.py
