#  tests/80_liquid_clean.py
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
"""
Tests the cleaners, which remove the opcodes which your favorite SFZ players do
not support.
"""
import logging
from re import compile as rcompile
from sfzen import *
from . import *
from sfzen.cleaners.liquidsfz import clean as liquid_clean


def test_reverse_header_walk(good_sfzs):
	for sfz in good_sfzs:
		header_ids = []
		for element, _ in sfz.walk():
			if isinstance(element, Header):
				header_ids.append(id(element))
		for element, _ in sfz.reverse_header_walk():
			if isinstance(element, Header):
				assert id(element) == header_ids.pop()

def test_liquid_clean(good_sfzs):
	sfz = specific_sfz(good_sfzs, 'SFZ with elements liquidsfz does not support')
	assertion_regex = rcompile(r'assert-removed\s(.+)')
	n = 0
	for element, _ in sfz.walk():
		if isinstance(element, Header):
			for m in assertion_regex.findall(element.comment.string):
				assert not element.opcode(m) is None
				n += 1
	assert n > 0
	liquid_clean(sfz)
	n = 0
	for element, _ in sfz.walk():
		if isinstance(element, Header):
			for m in assertion_regex.findall(element.comment.string):
				assert element.opcode(m) is None
				n += 1
	assert n > 0

#  end tests/80_liquid_clean.py
