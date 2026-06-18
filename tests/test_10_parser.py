#  tests/test_10_parser.py
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
from sfzen import *
from sfzen.parser import *
from . import *


def test_instantiation(good_sfz_paths):
	for path in good_sfz_paths:
		parser = Parser(path)
		assert isinstance(parser, Parser)

def test_iteration(good_sfz_paths):
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			assert isinstance(match, ParseMatch)
			assert isinstance(match.line, int)
			assert isinstance(match.start, int)
			assert isinstance(match.end, int)

def test_header_values(good_sfz_paths):
	n = 0
	header_names = [ cls.__name__.lower() for cls in Header.__subclasses__() ]
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, HeaderMatch):
				assert match.header_name.lower() in header_names
				n += 1
	assert n > 0

def test_comment_match(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, CommentMatch):
				assert isinstance(match.string, str)
				assert len(match.string) > 0
				assert match.string[0:2] == '//'
				n += 1
	assert n > 0

def test_define_match(good_sfz_paths):
	parser = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with defines'))
	n = 0
	for match in parser:
		if isinstance(match, DefineMatch):
			assert match.string[0:7] == '#define'
			assert match.key in ['ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff']
			assert 16 <= int(match.value) <= 112
			n += 1
	assert n > 0

def test_opcode_match(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch):
				assert isinstance(match.key, str)
				assert len(match.key) > 0
				assert isinstance(match.value, str)
				assert len(match.value) > 0
				n += 1
	assert n > 0

def test_opcode_with_comment(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch) and \
				isinstance(match.comment, CommentMatch):
				n += 1
	assert n > 0

def test_two_opcodes_on_line(good_sfz_paths):
	n = 0
	last_match = None
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch):
				if isinstance(last_match, OpcodeMatch) and \
					last_match.line == match.line:
					n += 1
				last_match = match
	assert n > 0

def test_two_opcodes_on_line_one_comment(good_sfz_paths):
	n = 0
	last_match = None
	for path in good_sfz_paths:
		parser = Parser(path)
		for match in parser:
			if isinstance(match, OpcodeMatch):
				if match.comment \
					and isinstance(last_match, OpcodeMatch) \
					and last_match.comment \
					and last_match.comment.string == match.comment.string:
					n += 1
				last_match = match
	assert n > 0

def test_spaces_in_samples(good_sfz_paths):
	p_simple = Parser(specific_sfz_path(good_sfz_paths, 'Simple SFZ'))
	p_spaces = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with spaces in sample names'))
	n = 0
	for m_simple, m_spaces in zip(p_simple, p_spaces):
		assert m_simple.__class__ == m_spaces.__class__
		if isinstance(m_simple, OpcodeMatch) and m_simple.key.lower() == 'sample':
			assert m_simple.value.replace('_', ' ') == m_spaces.value
			n += 1
	assert n > 0

def test_include_match(good_sfz_paths):
	parser = Parser(specific_sfz_path(good_sfz_paths, 'SFZ with included defines in same directory'))
	n = 0
	for match in parser:
		if isinstance(match, IncludeMatch):
			assert isinstance(match.filename, str)
			assert match.filename == 'defines.sfz'
			n += 1
	assert n > 0


#  end tests/test_10_parser.py
