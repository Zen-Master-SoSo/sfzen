#  sfzen/scripts/sfz_opcode_usage.py
#
#  Copyright 2025 liyang <liyang@veronica>
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
Utility which lists all opcodes declared in one or many .sfz files
"""
import logging, argparse
from os.path import isdir, isfile, join
from glob import glob
from lark.exceptions import LarkError
from progress.bar import IncrementalBar
from sfzen import SFZ
from sfzen.sort import name_sorted


def main():
	"""
	Entry point, defined so as to make it easy to reference from bin script.
	"""
	parser = argparse.ArgumentParser()
	parser.epilog = """
	List all the opcodes used by the given SFZ[s].
	"""
	parser.add_argument('Filename', type=str, nargs='+',
		help='File or directory to inspect.')
	parser.add_argument("--recurse", "-r", action="store_true",
		help="Recurse into subdirectories.")
	parser.add_argument("--verbose", "-v", action="store_true",
		help="Show more detailed debug information.")
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)3d] %(message)s"
	)

	for path in options.Filename:
		if isdir(path):
			file_list = glob(join(path, '*.sfz'))
			if options.recurse:
				file_list.extend(glob(join(path, '**', '*.sfz')))
		elif isfile(path):
			file_list = [path]
	opcodes = set()
	with IncrementalBar('Reading .sfz', max=len(file_list)) as progress_bar:
		for filename in file_list:
			try:
				opcodes |= SFZ(filename).opcodes_used()
			except LarkError:
				print()
				print(f'Parse error in "{filename}"')
			progress_bar.next()
	print("\n".join(name_sorted(opcodes)))


if __name__ == "__main__":
	main()


#  end sfzen/scripts/sfz_opcode_usage.py
