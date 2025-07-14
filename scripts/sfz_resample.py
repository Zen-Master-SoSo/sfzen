#  sfzen/scripts/sfz_resample.py
#
#  Copyright 2025 liyang <liyang@veronica>
#
"""
Resamples sample files to another bitrate/depth/format.
Optionally converts stereo samples to mono.
"""
import logging, argparse
from os.path import join
from glob import glob
from progress.bar import IncrementalBar
from sfzen import SFZ


def main():
	"""
	Entry point, defined so as to make it easy to reference from bin script.
	"""
	parser = argparse.ArgumentParser()
	parser.epilog = """
	List all the opcodes used by the given SFZ[s].
	"""
	parser.add_argument('Filename', type=str, nargs='+',
		help='File or directory to inspect.')
	parser.add_argument("--mono", "-m", action="store_true",
		help="Also mixdown stereo samples to mono.")
	parser.add_argument("--recurse", "-r", action="store_true",
		help="Recurse into subdirectories.")
	parser.add_argument("--verbose", "-v", action="store_true",
		help="Show more detailed debug information.")
	options = parser.parse_args()
	log_level = logging.DEBUG if options.verbose else logging.ERROR
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = log_level, format = log_format)

	for path in options.Filename:
		if os.path.isdir(path):
			file_list = glob(join(path, '*.sfz'))
			if options.recurse:
				file_list.extend(glob(join(path, '**', '*.sfz')))
		elif os.path.isfile(path):
			file_list = [path]


if __name__ == "__main__":
	main()

#  end sfzen/scripts/sfz_resample.py
