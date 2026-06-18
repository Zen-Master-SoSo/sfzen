#  tests/test_20_element_basics.py
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
from sfzen.parser import (
	Parser,
	CommentMatch,
	HeaderMatch,
	IncludeMatch,
	DefineMatch,
	OpcodeMatch,
)
from sfzen import *
from sfzen import replace_defs, HEADER_CLASSES
from . import *


def test_element_match(good_sfz_paths):
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			e = Element(match = match)
			assert e.match == match

def test_comment_instantiation(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, CommentMatch):
				e = Comment(match.string, match = match)
				assert isinstance(e, Comment)
				assert isinstance(e.string, str)
				assert len(e.string) > 0
				assert e.match == match
				n += 1
	assert n > 0

def test_header_instantiation(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, HeaderMatch):
				e = HEADER_CLASSES[match.header_name.lower()]()
				assert e.__class__.__name__.lower() == match.header_name
				n += 1
	assert n > 0

def test_opcode_instantiation(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch):
				e = Opcode(match.key, match.value)
				assert isinstance(e, Opcode)
				n += 1
	assert n > 0

def test_sample_instantiation(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch) and match.key.lower() == 'sample':
				e = Opcode(match.key, match.value)
				assert isinstance(e, Sample)
				n += 1
	assert n > 0

def test_spaces_in_samples(good_sfz_paths):
	parser = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with spaces in sample names'))
	n = 0
	for match in parser:
		if isinstance(match, OpcodeMatch) and match.key.lower() == 'sample':
			e = Opcode(match.key, match.value)
			assert isinstance(e, Sample)
			n += 1
	assert n > 0

def test_define_instantiation(good_sfz_paths):
	parser = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with defines'))
	n = 0
	for match in parser:
		if isinstance(match, DefineMatch):
			e = Define(match.key, match.value)
			assert isinstance(e, Define)
			n += 1
	assert n > 0

def test_define_replacements(good_sfz_paths):
	parser = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with defines'))
	defines = {}
	n = 0
	for match in parser:
		if isinstance(match, DefineMatch):
			e = Define(match.key, match.value)
			defines[e.varname] = e.value
		elif isinstance(match, OpcodeMatch):
			e = Opcode(replace_defs(match.key, defines), replace_defs(match.value, defines))
			if '$' in match.key:
				assert '$' not in e.name
			if '$' in match.value:
				assert not isinstance(e.value, str) or not '$' in e.value
			n += 1
	assert n > 0

def test_include_instantiation(good_sfz_paths):
	sfz_filename = specific_sfz_path(good_sfz_paths, 'SFZ with included defines in same directory')
	parser = Parser(sfz_filename)
	sfz_path = Path(sfz_filename)
	defines = {}
	n = 0
	for match in parser:
		if isinstance(match, DefineMatch):
			e = Define(match.key, match.value)
			defines[e.varname] = e.value
		elif isinstance(match, IncludeMatch):
			e = Include(match.filename)
			assert isinstance(e, Include)
			assert isinstance(e, Header)
			assert isinstance(e.path, Path)
			assert e.path.name == 'defines.sfz'
			assert e.filename is not None
			n += 1
	assert n > 0


#  end tests/test_20_element_basics.py
