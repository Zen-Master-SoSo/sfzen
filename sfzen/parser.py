#  sfzen/parser.py
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
Classes and functions used to interpret an SFZ file.
"""
from os import linesep
from re import compile as rcompile


def unquote(var):
	"""
	Remove quotes around a parsed value.
	"""
	for q in ["'", '"']:
		if var[0] == q and var[-1] == q:
			return var[1:-1]
	return var


class Parser:
	"""
	This class interprets the struture of an SFZ file and provides ParseMatch
	objects as it does. It does not create an SFZ file.
	"""

	def __init__(self, filename):
		"""
		Initialize the parser with the filename of the SFZ to parse.
		"""
		self.filename = filename
		self._current_block_comment = None
		self._current_element_comment = None

	def __iter__(self):
		"""
		Generator function which returns a ParseMatch object on each iteration.
		"""
		with open(self.filename) as fob:	# pylint: disable = unspecified-encoding
			for line_number, line in enumerate(fob.readlines()):
				line = line.strip()

				# Comments
				if len(line) == 0 and self._current_block_comment:
					yield self._current_block_comment
					self._current_block_comment = None
					continue

				self._current_element_comment = None
				if match := CommentMatch.match(line_number, line):
					line = line[:match.start].rstrip()
					if len(line):
						self._current_element_comment = match
					else:
						if self._current_block_comment:
							self._current_block_comment.string += f'{linesep}{match.string}'
							continue
						self._current_block_comment = match
						continue

				while len(line):
					# Header
					if match := HeaderMatch.match(line_number, line):
						yield from self._yield_with_comment(match)
					# Define
					elif match := DefineMatch.match(line_number, line):
						yield from self._yield_with_comment(match)
					# Include
					elif match := IncludeMatch.match(line_number, line):
						yield from self._yield_with_comment(match)
					# Opcodes
					elif match := OpcodeMatch.match(line_number, line):
						yield from self._yield_with_comment(match)
					# Unrecognized
					else:
						yield ParseError(self.filename, line_number)

					line = line[match.end:].strip()

	def _yield_with_comment(self, match):
		if self._current_block_comment:
			yield self._current_block_comment
			self._current_block_comment = None
		if self._current_element_comment:
			match.comment = self._current_element_comment
		yield match


class ParseMatch:
	"""
	This class contains the logic and regular expression used to match the sections
	of an SFZ file. Once a match is made, an instance of this class is returned
	with positional metadata, matched values, and related comment matches where
	applicable.
	"""

	regex = None
	comment = None

	@classmethod
	def match(cls, line_number, line):
		"""
		Returns an object of this class, if matched, else none
		"""
		if re_match := cls.regex.match(line):
			return cls(line_number, re_match)
		return None

	def __init__(self, line_number, re_match):
		self.line = line_number
		self.start = re_match.start()
		self.end = re_match.end()
		self.string = re_match.group(0).strip()

	def __str__(self):
		return self.string


class CommentMatch(ParseMatch):
	"""
	Searches for comment start (double slashes) anywhere on a line.
	"""

	regex = rcompile(r'\/\/\s*(.*)')

	@classmethod
	def match(cls, line_number, line):
		"""
		Returns a CommentMatch if matched, else none.
		"""
		if m := cls.regex.search(line):
			return cls(line_number, m)
		return None


class HeaderMatch(ParseMatch):
	"""
	Matches any "<header>" pattern
	"""

	regex = rcompile(r'<(\w+)>')

	def __init__(self, line_number, re_match):
		super().__init__(line_number, re_match)
		self.header_name = re_match.group(1)


class IncludeMatch(ParseMatch):
	"""
	Matches the "#include filename" pattern
	"""

	regex = rcompile(r'#include\s+(.*)')

	def __init__(self, line_number, re_match):
		super().__init__(line_number, re_match)
		self.filename = unquote(re_match.group(1).strip())


class KeyValueMatch(ParseMatch):
	"""
	Abstract base class of other match objects which contain a key/value pair.
	"""

	def __init__(self, line_number, re_match):
		super().__init__(line_number, re_match)
		self.key = re_match.group(1).strip()
		self.value = re_match.group(2).strip()


class DefineMatch(KeyValueMatch):
	"""
	Matches the "#define $varname value" pattern
	"""

	regex = rcompile(r'#define\s+\$([\w\$]+)\s+(.*)')


class OpcodeMatch(KeyValueMatch):
	"""
	Matches the "opcode_name=value" pattern
	"""

	regex = rcompile(r'([\w\$]+)=(.+)')
	opstart_regex = rcompile(r'([\w\$]+)=')

	@classmethod
	def match(cls, line_number, line):
		matches = list(cls.opstart_regex.finditer(line))
		if matches:
			if len(matches) > 1:
				line = line[:matches[1].start() - 1]
			return cls(line_number, cls.regex.match(line))
		return None


# ---------------------------
# Parse error

class ParseError(Exception):
	"""
	Custom exception raised when encountering parse errors.
	"""

	def __init__(self, filename, lineno):
		self.filename = filename
		self.lineno = lineno
		super().__init__(f'Parse error in {filename}, line {lineno}')


#  end sfzen/parser.py
