#  sfzen/resampler.py
#
#  Copyright 2025 liyang <liyang@veronica>
#
"""
Simple object-oriented SFZ parsing and manipulation.
"""
import logging
from os.path import join, basename, splitext
from tempfile import gettempdir as tempdir
import sox
from sfzen import SAMPLE_UNIT_OPCODES, SAMPLES_MOVE
from sfzen.sfz_elems import Opcode

class SFZResampler:

	def __init__(self, sfz, target_rate = 44100, target_channels = 1, target_bitdepth = 16):
		self.sfz = sfz
		self.target_rate = target_rate
		self.target_channels = target_channels
		self.target_bitdepth = target_bitdepth
		self.bad_samples = []

	def needs_resample(self):
		for sample in self.sfz.samples():
			resampler = SampleResampler(sample, self.target_rate, self.target_channels, self.target_bitdepth)
			if resampler.needs_resample():
				self.bad_samples.append(resampler)
		return bool(self.bad_samples)

	def resample_as(self, filename):
		for sample in self.sfz.samples():
			resampler = SampleResampler(sample, self.target_rate, self.target_channels, self.target_bitdepth)
			if resampler.needs_resample():
				resampler.resample()
		self.sfz.save_as(filename, SAMPLES_MOVE)


class SampleResampler:

	soxi_infos = {}			# { abspath : sox.file_info }
	converted_files = []	# Complicated filename in temp dir.

	def __init__(self, sample, target_rate, target_channels, target_bitdepth):
		self.sample = sample
		self.basedir = sample.basedir
		assert self.basedir is not None
		self.target_rate = target_rate
		self.target_channels = target_channels
		self.target_bitdepth = target_bitdepth
		self.source_path = self.sample.abspath
		if not self.source_path in self.soxi_infos:
			self.soxi_infos[self.source_path] = sox.file_info.info(self.source_path)
		for key, value in self.soxi_infos[self.source_path].items():
			setattr(self, key, value)

	@property
	def offset(self):
		opcode = self.sample.parent.opcode('offset')
		return opcode.value if opcode else 0

	@property
	def loop_start(self):
		opcode = self.sample.parent.opcode('loop_start') or self.sample.parent.opcode('loopstart')
		return opcode.value if opcode else 0

	@property
	def loop_end(self):
		opcode = self.sample.parent.opcode('loop_end') or self.sample.parent.opcode('loopend')
		return opcode.value if opcode else self.num_samples

	def needs_resample(self):
		return self.sample_rate != self.target_rate \
			or self.channels != self.target_channels \
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
				opcode = self.sample.parent.opcode(opcode_name)	# Retrieves inherited as well
				if opcode:
					adjusted_value = round(float(opcode.value) * ratio)
					if adjusted_value != opcode.value:
						self.sample.parent._opcodes[opcode_name] = Opcode(
							opcode_name, adjusted_value, None, self.basedir)
						logging.debug('Adjusted %s', opcode)
		# ------------------
		# Do file conversion
		filetitle, ext = splitext(basename(self.source_path))
		param_str = f'{self.target_rate}-{self.target_channels}-{self.target_bitdepth}'
		out_file = join(tempdir(), f'{filetitle}-{param_str}{ext}')
		if not out_file in self.converted_files:
			xfmr = sox.Transformer()
			xfmr.convert(
				samplerate = self.target_rate,
				n_channels = self.target_channels,
				bitdepth = self.target_bitdepth)
			xfmr.build_file(self.source_path, out_file)
			self.converted_files.append(out_file)
		self.sample.value = out_file


#  end sfzen/resampler.py
