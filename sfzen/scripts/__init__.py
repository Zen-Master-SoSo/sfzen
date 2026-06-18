#  sfzen/scripts/__init__.py
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
Provides functions which support common tasks used by all command-line scripts
in the sfzen package.
"""
from os import linesep
from sys import stderr
from pathlib import Path


def given_paths(options):
	"""
	Uses the command-line options parsed by argparse to return a list of SFZs.

	Returns a flat list of Path objects.
	"""
	path_list = []
	for filename in options.Filename:
		path = Path(filename)
		if path.exists():
			if path.is_dir():
				if options.recurse:
					path_list.extend(path.rglob('*.sfz'))
				else:
					stderr.write(f'"{path}" is a directory{linesep}')
			elif path.is_file():
				path_list.append(path)
		else:
			stderr.write(f'File not found: "{path}"{linesep}')
	return path_list


#  end sfzen/scripts/__init__.py
