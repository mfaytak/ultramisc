
'''
acq-share.py: by Matt Faytak / Jennifer Kuo
Divide ultrasound subdirectories into approximately
  equal shares for processing by multiple workers. 
  Usage: python acq-share.py [expdir] [shares] [--flat] [--random]
		 expdir: the experiment folder containing the acquisition 
		   subdirectories to be divided.
		 shares: the number of shares to divide the acquisitions
		   into.
		 --flat: if specified, assume the directory structure is
		   flat (all files in one folder, which is expdir).
		 --random: if specified, take randomly selected subsets
		   (otherwise, contiguous parts of sorted list are taken).
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
parser.add_argument("--flat","-f",
					action='store_true',
					help="If specified, expect a flat directory structure within expdir"
					)
parser.add_argument("--random","-r",
					action='store_true',
					help="If specified, divide pseudo-randomly into subsets; \
						  otherwise use contiguous parts of sorted file list"
					)
args = parser.parse_args()

try:
	expdir = args.expdir
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

coders = args.shares
counter = 0

if args.flat:

	# look through directory for all files matching basename;
	tg_glob = glob.glob(os.path.join(expdir, "*.ch1.TextGrid"))

	if not args.random:
		tg_glob.sort()

	for part in split(tg_glob, coders):
		# name output dir according to coder number
		counter += 1
		out = os.path.join(expdir,"_share{}".format(counter))
		os.makedirs(out)

		# go through and copy all files matching TG basename
		for tg in part:
			basename = os.path.split(tg)[-1].split('.')[0]
			matching_file_exp = os.path.join(expdir,str(basename + "*"))
			
			for f in glob.glob(matching_file_exp):
				out_dest = os.path.join(out,os.path.split(f)[-1])
				shutil.copy(f,out_dest)

else:

	# look into an additional layer of subdirectories, 
	# and copy contents of each subdir
	# TODO this also captures flattened dirs and all their contents.
	tg_glob = glob.glob(os.path.join(expdir, "*", "*.ch1.TextGrid"))

	if not args.random:
		tg_glob.sort()

	if len(tg_glob) == 0:
		print("WARNING: No TextGrids found. Are you supposed to be using --flat?")

	for part in split(tg_glob, coders):
		counter += 1
		out = os.path.join(expdir,"_out{}".format(counter))
		
		for tg in part:
			parent = os.path.dirname(tg)
			#print(parent)
			out_dest = os.path.join(out, os.path.split(parent)[-1])
			shutil.copytree(parent, out_dest)
