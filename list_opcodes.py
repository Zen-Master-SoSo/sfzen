#  sfzen/list_opcodes.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Utility which lists all opcodes declared in one or many .sfz files
"""
import os, sys, logging, argparse, glob
from sfzen import SFZ
from progress.bar import IncrementalBar


def main():
	parser = argparse.ArgumentParser()
	parser.epilog = """
	Write your help text!
	"""
	parser.add_argument('Filename', type=str, nargs='+',
		help='File or directory to inspect.')
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
			file_list = glob.glob(os.path.join(path, '*.sfz'))
			if options.recurse:
				file_list.extend(glob.glob(os.path.join(path, '**', '*.sfz')))
		elif os.path.isfile(path):
			file_list = [path]
	opcodes = set()
	with IncrementalBar('Reading .sfz', max=len(file_list)) as bar:
		for filename in file_list:
			opcodes |= SFZ(filename).opcodes_used()
			bar.next()
	print("\n".join(sorted(opcodes)))


if __name__ == "__main__":
	main()


#  end sfzen/list_opcodes.py
