#  sfzen/scripts/sfz_copy.py
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
Copies an .sfz to another location with multiple ways of handling samples.
"""
import os, sys, logging, argparse
from log_soso import log_error
from sfzen import (
	SFZ,
	SAMPLES_ABSPATH,
	SAMPLES_RESOLVE,
	SAMPLES_COPY,
	SAMPLES_SYMLINK,
	SAMPLES_HARDLINK
)


def main():
	p = argparse.ArgumentParser()
	p.add_argument('Source', type=str, help='SFZ file to copy from')
	p.add_argument('Target', type=str, nargs='?', help='Destination to copy to')
	p.add_argument("--simplify", "-S", action="store_true",
		help='Reduce the number of opcode declarations by forming groups which define common opcodes.')
	group = p.add_mutually_exclusive_group()
	group.add_argument("--abspath", "-a", action="store_true",
		help='Point to the original samples - absolute path')
	group.add_argument("--relative", "-r", action="store_true",
		help='Point to the original samples - relative path')
	group.add_argument("--copy", "-c", action="store_true",
		help='Copy samples to the "./samples" folder')
	group.add_argument("--symlink", "-s", action="store_true",
		help='Create symlinks in the "./samples" folder')
	group.add_argument("--hardlink", "-l", action="store_true",
		help='Hardlink samples in the "./samples" folder')
	p.add_argument("--dry-run", "-n", action="store_true",
		help="Do not make changes - just show what would be changed.")
	p.add_argument("--verbose", "-v", action="store_true",
		help="Show more detailed debug information")
	p.epilog = __doc__
	options = p.parse_args()
	if not os.path.isfile(options.Source):
		p.exit(f'"{options.Source}" is not a file')
	if not options.Target and not options.dry_run:
		p.error('<Target> is required when not --dry-run')
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)3d] %(message)s"
	)

	if options.abspath:
		samples_mode = SAMPLES_ABSPATH
	elif options.relative:
		samples_mode = SAMPLES_RESOLVE
	elif options.copy:
		samples_mode = SAMPLES_COPY
	elif options.symlink:
		samples_mode = SAMPLES_SYMLINK
	else:
		samples_mode = SAMPLES_HARDLINK

	sfz = SFZ(options.Source)
	if options.simplify:
		sfz = sfz.simplified()
	if options.dry_run:
		for sample in sfz.samples():
			sample.use_abspath()
		sfz.write(sys.stdout)
	else:
		target = options.Target
		if os.path.isdir(target):
			target = os.path.join(target, os.path.basename(options.Source))
		print(f'Copying {options.Source} to {target}')
		try:
			sfz.save_as(target, samples_mode)
		except OSError as err:
			if err.errno == 18:
				print(f'Error {err}')
				print('You probably tried to hardlink samples to a drive different from the one they are on.')
				print('\nTry another sample mode:\n')
				p.print_help()
			else:
				log_error(err)


if __name__ == '__main__':
	main()


#  end sfzen/scripts/sfz_copy.py
