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
from shutil import rmtree
from re import compile as rcompile
from sfzen import *
from . import *

# ---------------------------
# Support functions

def for_every_exported_sample(good_sfz_paths, tmp_path, samples_mode, func):
	export_dir = tmp_path / 'exported'
	for path in good_sfz_paths:
		sfz = SFZ(path)
		if export_dir.is_dir():
			rmtree(export_dir)
		export_filename = export_dir / 'root.sfz'
		src_filenames = [ str(sample.abspath) for sample in sfz.samples() ]
		sfz.save_as(export_filename, samples_mode = samples_mode)
		export = SFZ(export_filename)
		for src_filename, dest_sample in zip(src_filenames, export.samples()):
			func(src_filename, dest_sample)

def for_every_exported_sample_simplified(good_sfz_paths, tmp_path, samples_mode, func):
	export_dir = tmp_path / 'exported'
	for path in good_sfz_paths:
		sfz = SFZ(path).simplified()
		if export_dir.is_dir():
			rmtree(export_dir)
		export_filename = export_dir / 'root.sfz'
		src_filenames = [ str(sample.abspath) for sample in sfz.samples() ]
		sfz.save_as(export_filename, samples_mode = samples_mode)
		export = SFZ(export_filename)
		for src_filename, dest_sample in zip(src_filenames, export.samples()):
			func(src_filename, dest_sample)

def sample_contents_path(sample):
	return TEST_DIR_PATH.joinpath(sample.abspath.read_text().rstrip())


# ---------------------------
# Tests

def test_samples_content(good_sfz_paths):
	for path in good_sfz_paths:
		sfz = SFZ(path)
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

def test_samples_abspath(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert src_filename == str(dest_sample.path)
		assert src_filename == dest_sample.value
		assert src_filename == dest_sample.given_value
	for_every_exported_sample(good_sfz_paths, tmp_path, SAMPLES_ABSPATH, _test)

def test_samples_relpath(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert dest_sample.value[:2] == '..'
		assert str(dest_sample.path)[:2] == '..'
	for_every_exported_sample(good_sfz_paths, tmp_path, SAMPLES_RELPATH, _test)

def test_samples_copy(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		if not dest_sample.abspath.exists():
			logging.debug('sfz.abspath: %s', dest_sample.sfz.abspath)
			logging.debug('dest_sample.abspath: %s', dest_sample.abspath)
		assert dest_sample.exists()
		assert src_filename == str(sample_contents_path(dest_sample))
	for_every_exported_sample(good_sfz_paths, tmp_path, SAMPLES_COPY, _test)

def test_samples_symlink(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(sample_contents_path(dest_sample))
	for_every_exported_sample(good_sfz_paths, tmp_path, SAMPLES_SYMLINK, _test)

def test_samples_hardlink(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename != str(dest_sample.abspath)
		assert src_filename == str(sample_contents_path(dest_sample))
		src_stat = Path(src_filename).stat()
		dest_stat = dest_sample.abspath.stat()
		assert src_stat.st_nlink > 1
		assert dest_stat.st_nlink > 1
		assert src_stat.st_ino == dest_stat.st_ino
	for_every_exported_sample(good_sfz_paths, tmp_path, SAMPLES_HARDLINK, _test)


def test_samples_abspath_simplified(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert src_filename == str(dest_sample.path)
		assert src_filename == dest_sample.value
		assert src_filename == dest_sample.given_value
	for_every_exported_sample_simplified(good_sfz_paths, tmp_path, SAMPLES_ABSPATH, _test)

def test_samples_relpath_simplified(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(dest_sample.abspath)
		assert dest_sample.value[:2] == '..'
		assert str(dest_sample.path)[:2] == '..'
	for_every_exported_sample_simplified(good_sfz_paths, tmp_path, SAMPLES_RELPATH, _test)

def test_samples_copy_simplified(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		if not dest_sample.abspath.exists():
			logging.debug('sfz.abspath: %s', dest_sample.sfz.abspath)
			logging.debug('dest_sample.abspath: %s', dest_sample.abspath)
		assert dest_sample.exists()
		assert src_filename == str(sample_contents_path(dest_sample))
		assert src_filename
	for_every_exported_sample_simplified(good_sfz_paths, tmp_path, SAMPLES_COPY, _test)

def test_samples_symlink_simplified(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(sample_contents_path(dest_sample))
	for_every_exported_sample_simplified(good_sfz_paths, tmp_path, SAMPLES_SYMLINK, _test)

def test_samples_hardlink_simplified(good_sfz_paths, tmp_path):
	def _test(src_filename, dest_sample):
		assert src_filename == str(sample_contents_path(dest_sample))
		src_stat = Path(src_filename).stat()
		dest_stat = dest_sample.abspath.stat()
		assert src_stat.st_nlink > 1
		assert dest_stat.st_nlink > 1
		assert src_stat.st_ino == dest_stat.st_ino
	for_every_exported_sample_simplified(good_sfz_paths, tmp_path, SAMPLES_HARDLINK, _test)


#  end tests/test_70_save_as.py
