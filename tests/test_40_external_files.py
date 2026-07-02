#  tests/test_40_external_files.py
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


def test_sample_path(good_sfzs):
	n = 0
	for sfz in good_sfzs:
		for element, _ in sfz.walk():
			if isinstance(element, Sample):
				assert element.sfz is sfz
				assert isinstance(element.path, Path)
				assert isinstance(element.abspath, Path)
				assert element.abspath.exists()
				assert element.exists()
				n += 1
	assert n > 0

def test_include_path(good_sfzs):
	n = 0
	for sfz in good_sfzs:
		for element, _ in sfz.walk():
			if isinstance(element, Include):
				assert element.sfz is sfz
				assert isinstance(element.path, Path)
				assert isinstance(element.abspath, Path)
				assert element.abspath.exists()
				assert element.exists()
				n += 1
	assert n > 0

def test_include_define_instantiation(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ with included defines in same directory')
	for include in sfz.includes():
		assert include.exists()
	defines = list(sfz.defines())
	assert len(defines) > 5
	for define in defines:
		assert define.value.isnumeric()

def test_include_define_replacement(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ with included defines in same directory')
	defines = { define.varname:define.value for define in sfz.defines() }
	n = 0
	for element, _ in sfz.walk():
		if isinstance(element, Opcode) and element.given_value[0] == '$':
			varname = element.given_value[1:]
			assert varname in defines
			assert defines[varname] == str(element.value)
			assert defines[varname] == str(getattr(element.parent, element.name))
			n += 1
	assert n > 0


#  end tests/test_40_external_files.py
