#  tests/test_60_simplifying.py
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
from sfzen import *
from . import *


def test_clone(good_sfzs):
	n = 0
	nc = 0
	for sfz in good_sfzs:
		for elem, _ in sfz.reverse_header_walk():
			if not isinstance(elem, SFZ):
				clone = elem.clone()
				assert id(elem) != id(clone)
				n += 1
				for opcode in elem.opcodes().values():
					if opcode.comment is not None:
						clone = opcode.clone()
						assert clone.comment.string == opcode.comment.string
						nc += 1
	assert n > 0
	assert nc > 0

def test_clone_regions(good_sfzs):
	for sfz in good_sfzs:
		for region, clone in zip(sfz.regions(), sfz.clone_regions()):
			assert opcodes_to_opstrings(region.inherited_opcodes()) == \
				opcodes_to_opstrings(clone.opcodes())
			source_ids = set(id(opcode) for opcode in region.opcodes().values())
			assert len(source_ids) == len(region.opcodes())
			clone_ids = set(id(opcode) for opcode in clone.opcodes().values())
			assert len(clone_ids) == len(clone.opcodes())
			assert len(source_ids & clone_ids) == 0
			if sample := region.sample:
				cloned_sample = clone.sample
				assert sample.value == cloned_sample.value
				assert sample.path == cloned_sample.path
				assert id(sample.path) != id(cloned_sample.path)

def test_region_clone_isolation(good_sfz_paths):
	n = 0
	for path in good_sfz_paths:
		sfz = SFZ(path)
		for region, clone in zip(sfz.regions(), sfz.clone_regions()):
			region_keys = set(region.opcodes().keys())
			assert len(region.opcodes()) == len(region_keys)
			clone_keys = set(clone.opcodes().keys())
			assert len(clone.opcodes()) == len(clone_keys)
			if candidates := list(region_keys & clone_keys):
				if removals := candidates[:len(candidates) // 2]:
					clone.remove_opcodes(removals)
					assert len(set(clone.opcodes().keys()) & set(removals)) == 0
					assert len(set(region.opcodes().keys()) & set(removals)) == len(removals)
					n += 1
	assert n > 0

def test_condense_key(good_sfz_paths):
	sfz = SFZ(specific_sfz_path(good_sfz_paths, 'SFZ for reductions checking'))
	for region in sfz.regions():
		key = region.opcode('lokey').value
		region.condense_key_opcodes()
		assert region.opcode('lokey') is None
		assert region.opcode('hikey') is None
		assert region.opcode('pitch_keycenter') is None
		assert region.opcode('key').value == key

def test_remove_defaults(good_sfz_paths):
	sfz = SFZ(specific_sfz_path(good_sfz_paths, 'SFZ for reductions checking'))
	n = 0
	for region in sfz.regions():
		pre_len = len(region.opcodes())
		removals = [
			opcode.name for opcode in region.opcodes().values() \
			if opcode.comment and 'assert-removed-default' in opcode.comment.string
		]
		if len(removals):
			region.remove_defaults()
			assert len(region.opcodes()) + len(removals) == pre_len
			n += 1
	assert n > 0

def test_simplified(good_sfzs):
	for sfz in good_sfzs:
		simp = sfz.simplified()
		assert len(list(sfz.regions())) == len(list(simp.regions()))
		assert len(list(sfz.samples())) == len(list(simp.samples()))
		for sample in simp.samples():
			assert sample.path is not None
			assert sample.abspath is not None
			assert isinstance(sample.path, Path)
			assert isinstance(sample.abspath, Path)

def test_simplification(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ for reductions checking')
	original_regions = sfz.clone_regions()
	assert len(original_regions) == 3
	for elem, _ in sfz.walk():
		if isinstance(elem, Opcode) and 'assert-promoted-to-key' in elem.comment.string:
			promoted_key = elem.value
	simp = sfz.simplified()
	assert simp.global_header().get_opcode_value('key') == promoted_key
	for original_region, simplified_region in zip(original_regions, simp.regions()):
		for opcode_name, opcode in original_region.opcodes().items():
			if 'assert-remains' in opcode.comment.string:
				opcode_clone = simplified_region.opcode(opcode_name)
				assert opcode_clone is not None
				assert 'assert-remains' in opcode_clone.comment.string
			elif 'assert-promoted-to-key' in opcode.comment.string:
				assert simplified_region.opcode(opcode_name) is None
			elif isinstance(opcode, Sample):
				assert 'assert-comment-copied' in opcode.comment.string


#  tests/test_60_simplifying.py
