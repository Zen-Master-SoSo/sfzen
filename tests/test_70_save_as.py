#  tests/test_70_save_as.py
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
from shutil import rmtree, copytree
from re import compile as rcompile
from sfzen import *
from . import *

# ---------------------------
# Support functions

def source_and_target(tmp):
	"""
	Generator which copies every test sfz source tree to a temporary folder,
	creates a destination tree, and yields.

	So:
		sfzen/tests/sfzs/good/<tree>
	...is copied to...
		tmp/source/<tree>
	...and an empty target directory is created at...
		tmp/target/<tree>

	We do this because the test sfz dir may not be on the same drive as the system
	temp dir, and attempting to hard-link across drives will fail.

	Yields tuple (source_dir, source_sfz, target_dir, target_filename)
	"""
	for zen_test_path in sorted(list(Path(TEST_DIR_PATH, 'sfzs', 'good').iterdir())):
		source_dir = tmp / zen_test_path.name / 'source'
		target_dir = tmp / zen_test_path.name / 'target'
		target_filename = target_dir / 'root.sfz'
		assert not source_dir.is_dir()
		assert not target_dir.is_dir()
		copytree(zen_test_path, source_dir)
		source_sfz = None
		for filepath in source_dir.rglob('*.sfz'):
			if filepath.name == 'root.sfz':
				source_sfz = SFZ(filepath)
				break
		assert isinstance(source_sfz, SFZ)
		yield source_dir, source_sfz, target_dir, target_filename

def for_every_exported_sample(tmp, samples_mode, func):
	"""
	tmp: pytest temp_dir
	"""
	for source_dir, source_sfz, target_dir, target_filename in source_and_target(tmp):
		src_filenames = [ str(sample.abspath) for sample in source_sfz.samples() ]
		source_sfz.save_as(target_filename, samples_mode = samples_mode)
		target_sfz = SFZ(target_filename)
		for src_filename, dest_sample in zip(src_filenames, target_sfz.samples()):
			func(src_filename, dest_sample)

def for_every_exported_sample_simplified(tmp, samples_mode, func):
	for source_dir, source_sfz, target_dir, target_filename in source_and_target(tmp):
		sfz = source_sfz.simplified()
		src_filenames = [ str(sample.abspath) for sample in sfz.samples() ]
		sfz.save_as(target_filename, samples_mode = samples_mode)
		target_sfz = SFZ(target_filename)
		for src_filename, dest_sample in zip(src_filenames, target_sfz.samples()):
			func(src_filename, dest_sample)

def sample_content(filename):
	return Path(filename).read_text().rstrip()

def sample_contents_path(sample):
	return TEST_DIR_PATH.resolve().joinpath(sample.abspath.read_text().rstrip())


# ---------------------------
# Tests

def test_samples_content(good_sfzs):
	for sfz in good_sfzs:
		for sample in sfz.samples():
			assert sample_contents_path(sample) == sample.abspath

def test_merge_includes(good_sfz_paths):
	def inherited_element_count(header):
		return sum(len(element.elements) \
			for element, _ in header.walk() \
			if isinstance(element, Header))
	for title in [
		'SFZ with included region, samples beneath',
		'SFZ with included region, samples astride'
	]:
		sfz = SFZ(specific_sfz_path(good_sfz_paths, title))
		element_count = inherited_element_count(sfz)
		src_filenames = [ str(sample.abspath) for sample in sfz.samples() ]
		sfz.merge_includes()
		assert element_count > inherited_element_count(sfz)
		for src_filename, dest_sample in zip(src_filenames, sfz.samples()):
			assert src_filename == str(dest_sample.abspath)


def test_samples_abspath(tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert src_filename == str(dest_sample.path)
		assert src_filename == dest_sample.value
		assert src_filename == dest_sample.given_value
	for_every_exported_sample(tmp_path, SAMPLES_ABSPATH, _test)

def test_samples_relpath(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
		assert src_filename == str(dest_sample.abspath)
		assert dest_sample.value[:2] == '..'
		assert str(dest_sample.path)[:2] == '..'
	for_every_exported_sample(tmp_path, SAMPLES_RELPATH, _test)

def test_samples_copy(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
	for_every_exported_sample(tmp_path, SAMPLES_COPY, _test)

def test_samples_symlink(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
	for_every_exported_sample(tmp_path, SAMPLES_SYMLINK, _test)

def test_samples_hardlink(tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename != str(dest_sample.abspath)
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
		src_stat = Path(src_filename).stat()
		dest_stat = dest_sample.abspath.stat()
		assert src_stat.st_nlink > 1
		assert dest_stat.st_nlink > 1
		assert src_stat.st_ino == dest_stat.st_ino
	for_every_exported_sample(tmp_path, SAMPLES_HARDLINK, _test)


def test_samples_abspath_simplified(tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert src_filename == str(dest_sample.path)
		assert src_filename == dest_sample.value
		assert src_filename == dest_sample.given_value
	for_every_exported_sample_simplified(tmp_path, SAMPLES_ABSPATH, _test)

def test_samples_relpath_simplified(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
		assert src_filename == str(dest_sample.abspath)
		assert dest_sample.value[:2] == '..'
		assert str(dest_sample.path)[:2] == '..'
	for_every_exported_sample_simplified(tmp_path, SAMPLES_RELPATH, _test)

def test_samples_copy_simplified(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
		assert src_filename
	for_every_exported_sample_simplified(tmp_path, SAMPLES_COPY, _test)

def test_samples_symlink_simplified(tmp_path):
	def _test(src_filename, dest_sample):
		assert dest_sample.exists()
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
	for_every_exported_sample_simplified(tmp_path, SAMPLES_SYMLINK, _test)

def test_samples_hardlink_simplified(tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename != str(dest_sample.abspath)
		assert sample_content(src_filename) == sample_content(dest_sample.abspath)
		src_stat = Path(src_filename).stat()
		dest_stat = dest_sample.abspath.stat()
		assert src_stat.st_nlink > 1
		assert dest_stat.st_nlink > 1
		assert src_stat.st_ino == dest_stat.st_ino
	for_every_exported_sample_simplified(tmp_path, SAMPLES_HARDLINK, _test)


#  end tests/test_70_save_as.py
