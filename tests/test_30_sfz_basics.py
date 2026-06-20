#  tests/test_30_sfz_basics.py
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
from os import linesep
from pathlib import Path
from re import compile as rcompile
from sfzen import *
from . import *


def test_instantiation(good_sfz_paths):
	for path in good_sfz_paths:
		sfz = SFZ(path)
		assert isinstance(sfz, SFZ)
		assert isinstance(sfz.comment, Comment)
		assert linesep in sfz.comment.string

def test_walk_and_parents(good_sfzs):
	for sfz in good_sfzs:
		for element, depth in sfz.walk():
			assert isinstance(element, Element)
			assert isinstance(depth, int)
			if depth:
				assert isinstance(element.parent, Header)
				assert element.sfz is sfz

def test_header_walk(good_sfzs):
	for sfz in good_sfzs:
		list_1 = [ element for element, depth in sfz.walk() if isinstance(element, Header) ]
		list_2= [ element for element, depth in sfz.header_walk() ]
		for element in list_1:
			assert isinstance(element, Header)
		for element in list_2:
			assert isinstance(element, Header)
		assert len(list_1) == len(list_2)

def test_subheader_retrieval(good_sfzs):
	for sfz in good_sfzs:
		for header in sfz.subheaders():
			assert isinstance(header, Header)
			assert header.sfz is sfz

def test_region_retrieval(good_sfzs):
	for sfz in good_sfzs:
		for region in sfz.regions():
			assert isinstance(region, Region)
			assert region.sfz is sfz

def test_sample_retrieval(good_sfzs):
	for sfz in good_sfzs:
		for sample in sfz.samples():
			assert isinstance(sample, Sample)
			assert sample.sfz is sfz

def test_global_header_insertion(good_sfzs):
	for sfz in good_sfzs:
		global_header = sfz.global_header()
		assert isinstance(global_header, Global)
		for element in sfz.elements:
			if not isinstance(element, Comment):
				assert element is global_header
				assert element.sfz is sfz
				break

def test_opcodes(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ for inheritance checking')
	n = 0
	assertion_regex = rcompile(r'assert-opcode\s(\w+)=(.+)')
	for element, depth in sfz.walk():
		if isinstance(element, Header):
			if m := assertion_regex.search(element.comment.string):
				assert str(element.opcode(m.group(1)).value) == m.group(2)
				n += 1
	assert n > 0

def test_iopcodes(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ for inheritance checking')
	n = 0
	assertion_regex = rcompile(r'assert-iopcode\s(\w+)=(.+)')
	for element, depth in sfz.walk():
		if isinstance(element, Header):
			if m := assertion_regex.search(element.comment.string):
				assert str(element.iopcode(m.group(1)).value) == m.group(2)
				n += 1
	assert n > 0

def test_iopcode_inheritance(good_sfz_paths):
	sfz = SFZ(specific_sfz_path(good_sfz_paths, 'SFZ for inheritance checking'))
	n = 0
	for region in sfz.regions():
		if region.opcode('ampeg_attack') is None:
			opcode = region.iopcode('ampeg_attack')
			assert opcode is sfz.global_header().opcode('ampeg_attack')
			opcode.value = 0.999
			break
	assert sfz.global_header().opcode('ampeg_attack').value == 0.999

def test_inherited_opcodes(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ for inheritance checking')
	n = 0
	assertion_regex = rcompile(r'len-inherited_opcodes\s(.+)')
	for region in sfz.regions():
		if m := assertion_regex.search(region.comment.string):
			assert len(region.inherited_opcodes()) == int(m.group(1))
			n += 1
	assert n > 0

def test_opcode_count(good_sfzs):
	def inherited_opcode_count(header):
		return sum(len(element.opcodes().values()) \
			for element, _ in header.walk() \
			if isinstance(element, Header))
	sfz = specific_sfz(good_sfzs, 'SFZ for inheritance checking')
	n = 0
	assertion_regex = rcompile(r'assert-inherited_opcode_count\s(.+)')
	for element, depth in sfz.walk():
		if isinstance(element, Header):
			if m := assertion_regex.search(element.comment.string):
				assert inherited_opcode_count(element) == int(m.group(1))
				n += 1
	assert n > 0

def test_remove_opcode(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	for region in sfz.regions():
		keys = set(region.opcodes().keys())
		opcode_name = list(keys).pop()
		region.remove_opcode(opcode_name)
		assert set(region.opcodes().keys()) == keys - set([opcode_name])

def test_remove_opcodes(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	for region in sfz.regions():
		keys = set(region.opcodes().keys())
		removals = list(keys)[:len(keys) // 2]
		region.remove_opcodes(removals)
		assert set(region.opcodes().keys()) == keys - set(removals)

def test_append_opcode(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	for region in sfz.regions():
		keys = set(region.opcodes().keys())
		appended_opcode = region.append_opcode('transpose', -1)
		assert isinstance(appended_opcode, Opcode)
		assert appended_opcode.sfz is sfz
		assert set(region.opcodes().keys()) == keys | set(['transpose'])

def test_append_subheader(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	for element, depth in sfz.walk():
		if isinstance(element, Header) and not isinstance(element, Region):
			names = [ child.__class__.__name__.lower() for child in element.elements ]
			element.append_subheader('region')
			names.append('region')
			assert [ child.__class__.__name__.lower() for child in element.elements ] == names

def test_element_str(good_sfzs):
	for sfz in good_sfzs:
		for elem, _ in sfz.walk():
			assert isinstance(elem.__str__(), str)

def test_comment_association(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'Simple SFZ')
	n = 0
	for element, depth in sfz.walk():
		if isinstance(element, Header):
			assert element.comment is not None
		elif isinstance(element, Opcode) \
			and element.name == 'hivel' \
			and element.value == 64:
			assert element.comment is not None
			n += 1
	assert n > 0

#  end tests/test_30_sfz_basics.py
