#  sfzen/resampler.py
#
#  Copyright 2025 liyang <liyang@veronica>
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
Provides class used to modify sample rate, bit depth, and number of channels of SFZ samples.
"""
import logging
from os.path import join, basename
from tempfile import gettempdir as tempdir
try:
	import sox
except ImportError:
	print("""
Oops! "sox" is not installed! Resampling depends upon it
(You may have installed sfzen without the [resample] option)
Install the "sox" python wrapper and try again:

   pip install sox
""")
	exit()
from sfzen import SAMPLE_UNIT_OPCODES, SAMPLES_MOVE
from sfzen.sfz_elems import Opcode


class SFZResampler:
	"""
	Class used to modify sample rate, bit depth, and number of channels of SFZ samples.
	"""

	def __init__(self, sfz, target_rate = 44100, target_mono = False, target_bitdepth = 16):
		self.sfz = sfz
		self.target_rate = target_rate
		self.target_mono = target_mono
		self.target_bitdepth = target_bitdepth
		self.resamplers = [
			SampleResampler(sample, self.target_rate, self.target_mono, self.target_bitdepth) \
			for sample in self.sfz.samples() ]
		self.bad_samplers = [ resampler for resampler in self.resamplers if resampler.needs_resample() ]

	def needs_resample(self):
		return bool(self.bad_samplers)

	def resample_as(self, filename):
		for resampler in self.resamplers:
			if resampler.needs_resample():
				resampler.resample()
		self.sfz.save_as(filename, SAMPLES_MOVE)


class SampleResampler:

	soxi_infos = {}			# { abspath : sox.file_info }
	converted_files = []	# Complicated filename in temp dir.

	def __init__(self, sample, target_rate, target_mono, target_bitdepth):
		self.sample = sample
		self.basedir = sample.basedir
		assert self.basedir is not None
		self.target_rate = target_rate
		self.target_mono = target_mono
		self.target_bitdepth = target_bitdepth
		self.source_path = self.sample.abspath
		if not self.source_path in self.soxi_infos:
			self.soxi_infos[self.source_path] = sox.file_info.info(self.source_path)
		for key, value in self.soxi_infos[self.source_path].items():
			setattr(self, key, value)

	@property
	def offset(self):
		return self.sample.parent.offset or 0

	@property
	def loop_start(self):
		return self.sample.parent.loop_start or self.sample.parent.loopstart or 0

	@property
	def loop_end(self):
		return self.sample.parent.loop_end or self.sample.parent.loopend or self.num_samples

	def needs_resample(self):
		return self.sample_rate != self.target_rate \
			or self.target_mono and self.channels > 1 \
			or self.bitdepth != self.target_bitdepth

	def resample(self):
		if not self.needs_resample():
			logging.debug('Not resampling %s - already in target format', basename(self.sample.path))
			return
		# -----------------------------------------------------
		# Rescale other opcodes affected if sample rate changed
		if self.sample_rate != self.target_rate:
			ratio = self.target_rate / self.sample_rate
			for opcode_name in SAMPLE_UNIT_OPCODES:
				opcode = self.sample.parent.iopcode(opcode_name)	# Retrieves inherited as well
				if opcode:
					adjusted_value = round(float(opcode.value) * ratio)
					if adjusted_value != opcode.value:
						self.sample.parent._opcodes[opcode_name] = Opcode(
							opcode_name, adjusted_value, None, self.basedir)
						logging.debug('Adjusted %s', opcode)
		# ------------------
		# Do file conversion
		out_file = join(tempdir(), basename(self.source_path))
		if not out_file in self.converted_files:
			xfmr = sox.Transformer()
			xfmr.convert(
				samplerate = self.target_rate,
				n_channels = 1 if self.target_mono else None,
				bitdepth = self.target_bitdepth)
			xfmr.build_file(self.source_path, out_file)
			self.converted_files.append(out_file)
		self.sample.value = out_file


#  end sfzen/resampler.py
