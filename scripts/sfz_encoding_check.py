#  sfzen/scripts/sfz_encoding_check.py
#
#  Copyright 2025 liyang <liyang@veronica>
#
"""
Utility which checks whether sfz samples are in the desired format.
"""
import logging, argparse
from os.path import basename, isdir, isfile, join
from glob import glob
from collections import defaultdict
from jack import Client
try:
	from jack import JackOpenError
except ImportError:
	from jack import JackError as JackOpenError
from sfzen import SFZ
from sfzen.resampler import SFZResampler


def main():
	"""
	Entry point, defined so as to make it easy to reference from bin script.
	"""

	try:
		with Client(name = basename(__file__), no_start_server = True) as client:
			default_samplerate = client.samplerate
	except JackOpenError:
		default_samplerate = 44100

	parser = argparse.ArgumentParser()
	parser.epilog = """
	List all the opcodes used by the given SFZ[s].
	"""
	parser.add_argument('Filename', type=str, nargs='+',
		help = 'File or directory to inspect.')
	parser.add_argument("--recurse", "-r", action = "store_true",
		help = "Recurse into subdirectories.")
	parser.add_argument("--sample-rate", "-s", type = int, default = default_samplerate)
	parser.add_argument("--mono", "-m", action = "store_true",
		help = 'Check if samples are monophonic')
	parser.add_argument("--bitdepth", "-b", type = int, default = 16)
	parser.add_argument("--verbose", "-v", action = "store_true",
		help = "Show more detailed debug information.")
	options = parser.parse_args()
	log_level = logging.DEBUG if options.verbose else logging.ERROR
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = log_level, format = log_format)

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
		except OSError as e:
			print(f'Error in {filename}: {e}')
		else:
			if resampler.needs_resample():
				print(sfz.filename)
				if options.verbose:
					for bad_sample in resampler.bad_samplers:
						print(f"\t{bad_sample.sample.abspath}   " + \
							f"{bad_sample.sample_rate} Hz  " + \
							f"{bad_sample.channels} chan  " + \
							f"{bad_sample.bitdepth} bits")
				else:
					counts = defaultdict(int)
					for sresmpler in resampler.bad_samplers:
						counts[sresmpler.format_repr()] += 1
					for fmt, cnt in counts.items():
						print(f'\t{cnt} {fmt}')

if __name__ == "__main__":
	main()


#  end sfzen/scripts/sfz_encoding_check.py
