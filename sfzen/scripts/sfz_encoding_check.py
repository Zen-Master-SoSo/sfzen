#  sfzen/scripts/sfz_encoding_check.py
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
Utility which checks whether sfz samples are in the desired format.
"""
import logging, argparse
from os.path import isdir, isfile, join
from glob import glob
from collections import defaultdict
from sfzen import SFZ
from sfzen.resampler import SFZResampler


def main():
	"""
	Entry point, defined so as to make it easy to reference from bin script.
	"""

	parser = argparse.ArgumentParser()
	parser.epilog = """
	Check the format of samples used by the given SFZ(s).
	"""
	parser.add_argument('Filename', type=str, nargs='+',
		help = 'File or directory to inspect.')
	parser.add_argument("--sample-rate", "-s", type = int, default = 48000)
	parser.add_argument("--bitdepth", "-b", type = int, default = 16)
	parser.add_argument("--mono", "-m", action = "store_true",
		help = 'Check if samples are monophonic')
	parser.add_argument("--recurse", "-r", action = "store_true",
		help = "Recurse into subdirectories.")
	parser.add_argument("--verbose", "-v", action = "store_true",
		help = "Show more detailed debug information.")
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)3d] %(message)s"
	)

	for path in options.Filename:
		if isdir(path):
			file_list = glob(join(path, '*.sfz'))
			if options.recurse:
				file_list.extend(glob(join(path, '**', '*.sfz')))
		elif isfile(path):
			file_list = [path]

	for filename in sorted(file_list):
		try:
			sfz = SFZ(filename)
			resampler = SFZResampler(sfz,
				target_rate = options.sample_rate,
				target_mono = options.mono,
				target_bitdepth = options.bitdepth
			)
		except Exception as e:
			print(f'Error in "{filename}": {e}')
		else:
			if resampler.needs_resample():
				print(sfz.filename)
				if options.verbose:
					for bad_sample in resampler.bad_samplers:
						print(f"   {bad_sample.sample.abspath}   " + \
							f"{bad_sample.sample_rate} Hz  " + \
							f"{bad_sample.channels} chan  " + \
							f"{bad_sample.bitdepth} bits")
				else:
					counts = defaultdict(int)
					for samp_resampler in resampler.bad_samplers:
						fmt = f'{samp_resampler.sample_rate}Hz  {samp_resampler.bitdepth} bits  {samp_resampler.channels} channels'
						counts[fmt] += 1
					for fmt, cnt in counts.items():
						print(f'   {cnt:2d}  {fmt}')


if __name__ == "__main__":
	main()


#  end sfzen/scripts/sfz_encoding_check.py
