#  pylint: disable = duplicate-code
#
#  sfzen/scripts/sfz_liquid_safe.py
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
Strips an SFZ of opcodes which liquidsfz does not support.
"""
import sys, logging, argparse
from progress.bar import PixelBar
from sfzen import LOG_FORMAT, SFZ
from sfzen.cleaners.liquidsfz import clean
from . import given_paths


def main():
	"""
	Entry point for importing script from elsewhere.
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('Filename', type = str, nargs = '+',
		help = 'SFZ file name, or directory (with "--recurse").')
	parser.add_argument('--recurse', '-r', action = 'store_true',
		help = 'Recurse into subdirectories.')
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information')
	parser.epilog = __doc__
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = LOG_FORMAT
	)

	if path_list := given_paths(options):
		try:
			do_operations(path_list)
		except KeyboardInterrupt:
			print()
			return 3
	return 0


def do_operations(path_list):
	with PixelBar('Cleaning SFZs', max = len(path_list)) as progress_bar:
		for path in path_list:
			sfz = SFZ(path)
			clean(sfz)
			sfz.save()
			progress_bar.next()


if __name__ == '__main__':
	sys.exit(main() or 0)


#  end sfzen/scripts/sfz_liquid_safe.py
