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
Prints paths to samples used in a given SFZ. By default, prints the path relative to the SFZ.
"""
import sys, logging, argparse
from os.path import relpath
from operator import and_, or_
from functools import reduce
from sfzen import SFZ
from . import given_paths


def main():
	"""
	Entry point for importing script from elsewhere.
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('Filename', type = str, nargs = '+',
		help = 'SFZ file name, or directory (with "--recurse").')
	set_options = parser.add_mutually_exclusive_group()
	set_options.add_argument('--common', '-c', action = 'store_true',
		help = 'Only show paths common to all given files.')
	set_options.add_argument('--exclusive', '-e', action = 'store_true',
			help = 'Only show paths which are exclusive to one given file.')
	path_options = parser.add_mutually_exclusive_group()
	path_options.add_argument('--abspath', '-a', action = 'store_true',
		help = 'Show the absolute path to each sample, with symlinks resolved.')
	path_options.add_argument('--relpath', '-l', action = 'store_true',
		help = 'Show the path of each sample relative to the current working directory.')
	parser.add_argument("--recurse", "-r", action = "store_true",
		help = 'Recurse into subdirectories.')
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information.')
	parser.epilog = __doc__
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = '[%(filename)24s:%(lineno)3d] %(message)s'
	)

	if path_list := given_paths(options):
		try:
			do_operations(path_list, options)
		except KeyboardInterrupt:
			print()
			return 3
	return 0

def do_operations(path_list, options):
	sets = [ sample_paths(path, options) for path in path_list ]
	if options.common:
		paths = reduce(and_, sets)
	elif options.exclusive:
		paths = reduce(or_, sets, set()) ^ reduce(and_, sets)
	else:
		paths = reduce(or_, sets, set())
	if paths:
		for path in paths:
			print(path)


def sample_paths(filename, options):
	"""
	Returns set
	"""
	sfz = SFZ(filename)
	if options.abspath or options.relpath:
		paths = [ sample.abspath for sample in sfz.samples() ]
		return set(relpath(f) for f in paths) if options.relpath else set(paths)
	return set(sample.path for sample in sfz.samples())


if __name__ == '__main__':
	sys.exit(main() or 0)


#  end sfzen/scripts/sfz_liquid_safe.py
