#  pylint: disable = duplicate-code
#
#  sfzen/scripts/sfz_validate.py
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
Checks whether SFZ files are formatted correctly, and opcode values are of the
correct type and have valid values.
"""
import sys, logging, argparse
from collections import defaultdict
from progress.bar import PixelBar
from sfzen import LOG_FORMAT, SFZ
from . import given_paths

PROGRESS_BAR_MESSAGE = 'Reading SFZs'

def main():
	"""
	Entry point for importing script from elsewhere.
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('Filename', type = str, nargs = '+',
		help = 'SFZ file name (or directory with "--recurse").')
	group = parser.add_mutually_exclusive_group()
	group.add_argument('--quiet', '-q', action = 'store_true',
		help = 'Print nothing; the return value of this script reflects pass/fail condition.')
	group.add_argument('--summary', '-s', action = 'count',
		help = """Print a summary.
		If given once, the total count of each type of error encountered is printed.
		If given twice, the count of each unique instance of each error is printed.
		""")
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information.')
	parser.add_argument('--recurse', '-r', action = 'store_true',
		help = 'Recurse into subdirectories.')
	parser.epilog = __doc__
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = LOG_FORMAT
	)

	if path_list := given_paths(options):
		try:
			if options.quiet:
				return do_quiet(path_list)
			if options.summary == 1:
				return do_summary(path_list)
			if options.summary == 2:
				return do_strings(path_list)
			return do_detail(path_list)
		except KeyboardInterrupt:
			print()
			return 3
	return 0


def do_quiet(path_list):
	def _retval(path):
		try:
			return bool(SFZ(path).errors)
		except Exception:	# pylint: disable = broad-exception-caught
			return True
	return 1 if any(_retval(path) for path in path_list) else 0


def do_summary(path_list):
	summary_counts = defaultdict(int)
	def _append_err(err):
		summary_counts[type(err).__name__] += 1
	with PixelBar(PROGRESS_BAR_MESSAGE, max = len(path_list)) as progress_bar:
		for path in path_list:
			try:
				sfz = SFZ(path)
			except Exception as err:	# pylint: disable = broad-exception-caught
				_append_err(err)
			else:
				for err in sfz.errors:
					_append_err(err)
			progress_bar.next()
	for key, count in summary_counts.items():
		print(f' {count:4d} {key}')
	return 1 if summary_counts else 0


def do_strings(path_list):
	class ElemDict(defaultdict):
		"""
		Quick defaultdict used to count dict keys
		"""
		def __init__(self):
			super().__init__(int)
	has_errors = False
	summary_counts = defaultdict(ElemDict)
	with PixelBar(PROGRESS_BAR_MESSAGE, max = len(path_list)) as progress_bar:
		for path in path_list:
			try:
				sfz = SFZ(path)
			except Exception:	# pylint: disable = broad-exception-caught
				has_errors = True
			else:
				for err in sfz.errors:
					summary_counts[type(err).__name__][err.match.string] += 1
			progress_bar.next()
	for error_type, str_counts in summary_counts.items():
		count = sum(str_count for str_count in str_counts.values())
		print(f' {count:4d} {error_type}')
		for str_count, count in str_counts.items():
			print(f'    {count:4d} {str_count}')
	return 1 if has_errors or len(summary_counts) > 0 else 0


def do_detail(path_list):
	has_errors = False
	for path in path_list:
		try:
			sfz = SFZ(path)
		except Exception as err:	# pylint: disable = broad-exception-caught
			print(f'{path}: {err}')
			has_errors = True
		else:
			has_errors |= len(sfz.errors) > 0
			for err in sfz.errors:
				print(f'{path}:{err.match.line} "{err.match.string}": {err.origin}')
	return 1 if has_errors else 0


if __name__ == '__main__':
	sys.exit(main() or 0)


#  end sfzen/scripts/sfz_validate.py
