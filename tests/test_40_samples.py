#  tests/test_40_samples.py
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
import logging
from pathlib import Path
from sfzen import *
from . import *


def test_path_construction(good_sfzs):
	n = 0
	for sfz in good_sfzs:
		for element, _ in sfz.walk():
			if isinstance(element, Sample):
				assert isinstance(element.path, Path)
				assert isinstance(element.abspath, Path)
				assert element.abspath.exists()
				assert element.exists()
				n += 1
	assert n > 0

#  end tests/test_40_samples.py
