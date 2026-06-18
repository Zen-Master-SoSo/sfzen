#  tests/test_50_validation.py
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
from re import compile as rcompile
from midi_notes import Note
from sfzen import *
from sfzen import OPCODES, KEY_TYPE_OPCODES, Validator, PitchValidator
from . import *

def test_validators():
	"""
	Ensure that all opcodes have a good working Validator, implying that their
	definition is usable. Some opcodes had descriptive values for min, max, or
	default. This check makes sure that those oddities have been addresses.
	"""
	for opcode_name in OPCODES:
		validator = Validator.get_validator(opcode_name)
		try:
			validator.default_value
		except ValueError as e:
			logging.warning('Could not get default value for "%s" (%s)',
				opcode_name, e)
			raise e

def test_bad_values(bad_sfz_paths):
	sfz = SFZ(specific_sfz_path(bad_sfz_paths, 'Bad values'))
	assert_regex = rcompile(r'assert-(\w+)')
	n = 0
	for elem, _ in sfz.walk():
		if isinstance(elem, Opcode):
			m = assert_regex.search(elem.comment.string)
			if m:
				assert elem.error.__class__.__name__ == m.group(1)
				if not elem.error is None:
					n += 1
	assert n > 0
	assert len(sfz.errors) == n

def test_bad_tokens(bad_sfz_paths):
	sfz = SFZ(specific_sfz_path(bad_sfz_paths, 'Bad tokens'))
	assert_regex = rcompile(r'assert-(\w+)')
	n = 0
	for elem, _ in sfz.walk():
		if isinstance(elem, Opcode):
			m = assert_regex.search(elem.comment.string)
			if m:
				assert elem.error.__class__.__name__ == m.group(1)
				if not elem.error is None:
					n += 1
		elif isinstance(elem, Header):
			m = assert_regex.search(elem.comment.string)
			if m:
				assert elem.error.__class__.__name__ == m.group(1)
				if not elem.error is None:
					n += 1
	assert n > 0

def test_missing_samples(bad_sfz_paths):
	sfz = SFZ(specific_sfz_path(bad_sfz_paths, 'Missing samples'))
	n = 0
	for elem, _ in sfz.walk():
		if isinstance(elem, Sample):
			assert isinstance(elem.error, NotFoundError)
			n += 1
	assert n == 3
	assert len(sfz.errors) == n

def test_missing_include(bad_sfz_paths):
	sfz = SFZ(specific_sfz_path(bad_sfz_paths, 'Missing include'))
	n = 0
	for elem, _ in sfz.walk():
		if isinstance(elem, Include):
			assert isinstance(elem.error, NotFoundError)
			n += 1
	assert n == 1
	assert len(sfz.errors) == n

def test_note_names(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	n = 0
	for element, depth in sfz.walk():
		if isinstance(element, Opcode) and element.name in KEY_TYPE_OPCODES:
			assert isinstance(element.validator, PitchValidator)
			if isinstance(element.given_value, Note):
				assert isinstance(element.value, int)
				n += 1

#  end tests/test_50_validation.py
