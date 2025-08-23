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
Strips an SFZ of opcodes which liquidsfz does not understand.
"""
import os, sys, logging, argparse
from sfzen import SFZ
from sfzen.cleaners.liquidsfz import clean


def main():
	p = argparse.ArgumentParser()
	p.add_argument('Source', type=str,
		help='SFZ file to clean up')
	p.add_argument('Target', type=str, nargs='?',
		help='Destination SFZ. If not provided, the original SFZ will be modified.')
	p.add_argument("--verbose", "-v", action="store_true",
		help="Show more detailed debug information")
	p.epilog = __doc__
	options = p.parse_args()
	if not os.path.isfile(options.Source):
		p.exit(f'"{options.Source}" is not a file')
	target = options.Target or options.Source
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)3d] %(message)s"
	)

	sfz = SFZ(options.Source)
	clean(sfz)
	if options.Target:
		sfz.save_as(options.Target)
	else:
		sfz.save()


if __name__ == '__main__':
	main()


#  end sfzen/scripts/sfz_liquid_safe.py
