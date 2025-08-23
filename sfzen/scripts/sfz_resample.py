#  sfzen/scripts/sfz_resample.py
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
Resamples sample files to another bitrate/depth/format.
Optionally converts stereo samples to mono.
"""
import logging, argparse
from os.path import basename
from jack import Client
try:
	from jack import JackOpenError
except ImportError:
	from jack import JackError as JackOpenError
from sfzen.resampler import SFZResampler
from sfzen import SFZ


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
	Modify the sample rate (and other properties) of the source samples of an SFZ file.
	"""
	parser.add_argument('Source', type = str, help = 'SFZ file to resample.')
	parser.add_argument('Target', type = str, nargs = '?', help = 'Target SFZ to save.')
	parser.add_argument("--rate", "-r",
		type = int, default = default_samplerate,
		help = f"Sample rate (default {default_samplerate})")
	parser.add_argument("--mono", "-m", action = "store_true",
		help = "Make samples monophonic.")
	parser.add_argument("--bitdepth", "-b",
		type = int, default = 16, help = "Bitdepth (default 16)")
	parser.add_argument("--verbose", "-v", action = "store_true",
		help = "Show more detailed debug information.")
	options = parser.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)3d] %(message)s"
	)

	sfz = SFZ(options.Source)
	SFZResampler(sfz,
		target_rate = options.rate,
		target_mono = options.mono,
		target_bitdepth = options.bitdepth
	).resample_as(options.Target or options.Source)


if __name__ == "__main__":
	main()

#  end sfzen/scripts/sfz_resample.py
