
'''
acq-share.py: divide ultrasound subdirectories into approximately
  equal shares for processing by multiple workers. 
  Usage: python ultra-splitter.py [expdir] [shares]
         expdir: the experiment folder containing the acquisition 
           subdirectories to be divided.
         shares: the number of shares to divide the acquisitions
           into.
'''

import argparse
import glob 
import os
import shutil
import sys

# this fcn courtesy of user tixxit at https://stackoverflow.com/a/2135920
def split(a, n):
	k, m = divmod(len(a), n)
	return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

# read in arguments
parser = argparse.ArgumentParser(description='Divide ultrasound data into approximately equal shares.')
parser.add_argument("expdir", 
					help="Experiment directory containing all subjects'\
						  acquisition subfolders"
					)
parser.add_argument("shares",
					type=int,
                    help="Number of shares to divide the data into"
                    )
# TODO option for flat directory structure?
args = parser.parse_args()

try:
	expdir = args.expdir
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

tg_glob_exp = os.path.join(expdir, "*", "*.ch1.TextGrid")

coders = args.shares # TODO make arguments
counter = 0

# TODO convert to "flat structure"
# TODO have "flat structure option"
for part in split(glob.glob(tg_glob_exp), coders):
	print("listy list")
	counter += 1
	out = os.path.join(expdir,"_out{}".format(counter))
	for tg in part:
		parent = os.path.dirname(tg)
		print(parent)
		out_dest = os.path.join(out, os.path.split(parent)[-1])
		shutil.copytree(parent, out_dest)
