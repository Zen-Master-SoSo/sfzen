#  tests/__init__.py
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
import pytest
from pathlib import Path
from sfzen import SFZ
from sfzen.parser import Parser, CommentMatch


TEST_DIR_PATH = Path(__file__).parent

def _good_sfz_paths():
	return _sfz_paths('good')

@pytest.fixture
def good_sfz_paths():
	return _good_sfz_paths()

@pytest.fixture
def good_sfzs():
	return list(SFZ(path) for path in _good_sfz_paths())

def _bad_sfz_paths():
	return _sfz_paths('bad')

@pytest.fixture
def bad_sfz_paths():
	return _bad_sfz_paths()

@pytest.fixture
def bad_sfzs():
	return list(SFZ(path) for path in _bad_sfz_paths())

def _sfz_paths(subdir):
	return sorted([p for p in Path(TEST_DIR_PATH, 'sfzs', subdir).rglob('root.sfz')])

def specific_sfz_path(sfz_paths, search_string):
	for path in sfz_paths:
		with open(path, 'r') as fob:
			if search_string in fob.read():
				return path
	raise RuntimeError(f'SFZ path not found containing "{search_string}"')

def specific_sfz(sfzs, search_string):
	for sfz in sfzs:
		if search_string in sfz.comment.string:
			return sfz
	raise RuntimeError(f'SFZ not found containing "{search_string}"')


#  end tests/__init__.py
