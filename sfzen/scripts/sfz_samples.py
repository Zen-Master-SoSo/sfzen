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
from os import linesep
from os.path import realpath, relpath
from operator import and_, or_, xor
from functools import reduce
from sfzen import SFZ


def sfz_paths(filename, options):
	"""
	Returns set
	"""
	sfz = SFZ(filename)
	if options.abspath or options.realpath or options.relpath:
		sample_paths = [ sample.abspath for sample in sfz.samples() ]
		if options.realpath:
			return set(realpath(f) for f in sample_paths)
		elif options.relpath:
			return set(relpath(f) for f in sample_paths)
		return set(sample_paths)
	return set(sample.relpath for sample in sfz.samples())


def main():
	p = argparse.ArgumentParser()
	p.add_argument('Filename', type = str, nargs = '+',
		help = 'SFZ file to clean up')
	set_options = p.add_mutually_exclusive_group()
	set_options.add_argument('--common', '-c', action = 'store_true',
		help = 'Only show paths common to all given files.')
	set_options.add_argument('--exclusive', '-e', action = 'store_true',
			help = 'Only show paths which are exclusive to one given file.')
	path_options = p.add_mutually_exclusive_group()
	path_options.add_argument('--abspath', '-a', action = 'store_true',
		help = 'Show the absolute path to each sample. (Use "--realpath" to resolve symlinks.)')
	path_options.add_argument('--realpath', '-r', action = 'store_true',
		help = 'Resolve symlinks and show the resolved absolute path to each sample.')
	path_options.add_argument('--relpath', '-l', action = 'store_true',
		help = 'Show the path of each sample relative to the current working directory.')
	p.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information')
	p.epilog = __doc__
	options = p.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = '[%(filename)24s:%(lineno)3d] %(message)s'
	)

	try:
		sets = [ sfz_paths(filename, options) for filename in options.Filename ]
	except OSError as e:
		print(e)
		return 1

	if options.common:
		files = reduce(and_, sets)
	elif options.exclusive:
		files = reduce(or_, sets, set()) ^ reduce(and_, sets)
	else:
		files = reduce(or_, sets, set())

	if files:
		print(linesep.join(sorted(files)))


if __name__ == '__main__':
	main()


#  end sfzen/scripts/sfz_liquid_safe.py
