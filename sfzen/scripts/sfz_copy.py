#  pylint: disable = duplicate-code
#
#  sfzen/scripts/sfz_copy.py
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
Copies an SFZ to another location with multiple ways of handling samples.
"""
import sys, logging, argparse
from os import linesep
from pathlib import Path
from sfzen import (
	LOG_FORMAT,
	SFZ,
	SAMPLES_ABSPATH,
	SAMPLES_RELPATH,
	SAMPLES_COPY,
	SAMPLES_SYMLINK,
	SAMPLES_HARDLINK
)


def main():
	"""
	Entry point for importing script from elsewhere.
	TODO: Return value
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('Source', type = str,
		help = 'SFZ file to copy from.')
	parser.add_argument('Target', type = str, nargs = '?',
		help = 'Destination to copy to.')
	parser.add_argument('--simplify', '-S', action = 'store_true',
		help = 'Create <group> and <global> headers defining common opcodes.')
	group = parser.add_mutually_exclusive_group()
	group.add_argument('--copy', '-c', action = 'store_true',
		help = 'Copy samples to the target samples folder (default).')
	group.add_argument('--symlink', '-s', action = 'store_true',
		help = 'Create symlinks in the target samples folder.')
	group.add_argument('--hardlink', '-l', action = 'store_true',
		help = 'Hardlink samples in the target samples folder.')
	group.add_argument('--abspath', '-a', action = 'store_true',
		help = 'Point to the original samples - absolute path.')
	group.add_argument('--relative', '-r', action = 'store_true',
		help = 'Point to the original samples - relative path.')
	parser.add_argument('--dry-run', '-n', action = 'store_true',
		help = 'Do not make changes - just show what would be changed.')
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information.')
	parser.epilog = __doc__
	options = parser.parse_args()
	source = Path(options.Source)
	if not source.exists():
		parser.exit(f'"{options.Source}" is not a file')
	if not options.Target and not options.dry_run:
		parser.error('<Target> is required when not --dry-run')
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = LOG_FORMAT
	)

	if options.abspath:
		samples_mode = SAMPLES_ABSPATH
	elif options.relative:
		samples_mode = SAMPLES_RELPATH
	elif options.hardlink:
		samples_mode = SAMPLES_HARDLINK
	elif options.symlink:
		samples_mode = SAMPLES_SYMLINK
	else:
		samples_mode = SAMPLES_COPY

	sfz = SFZ(source)
	if options.simplify:
		sfz = sfz.simplified()
	if options.dry_run:
		sfz.write(sys.stdout)
	else:
		target = Path(options.Target)
		if target.is_dir():
			target = target / source.name
		print(f'Copying...{linesep}    {source}{linesep} -> {target}')
		try:
			sfz.save_as(target, samples_mode = samples_mode)
		except OSError as err:
			print(f'Error {err}')
			if err.errno == 18:
				print('You probably tried to hardlink samples to a drive different from the one they are on.')
				print()
				print('Try another sample mode:')
				print()
				parser.print_help()


if __name__ == '__main__':
	sys.exit(main() or 0)


#  end sfzen/scripts/sfz_copy.py
