#!/usr/bin/env python

# subsetter.py: pick out a subset of acquisitions in an experiment directory.
# usage: python subsetter.py expdir

# TODO test both options (delete, not delete)

import argparse
import glob
import os
import shutil
import sys

from ultramisc.ebutils import read_stimfile, read_listfile

# parse argument(s)
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
parser.add_argument("distractors",
					help="Plaintext list of distractor words, \
						one per line")
parser.add_argument("-d",
					"--delete", 
					help="Delete distractor files in place \
						(default behavior is to move distractor \
						files to new location)",
					action="store_true"
					)
args = parser.parse_args()

expdir = os.path.normpath(args.expdir)

# desired analysis set; change as required
distractor_list = read_listfile("distractors.txt", deaccent=True)


# issue warning or set up copy location.
if args.delete:
	while True:
		try:
			warning = input("WARNING: this will delete non-target acqs. \
							Make sure your files are backed up. Press Y \
							to continue or N to exit.")
			assert warning in ["Y", "N"]
		except AssertionError:
			print("Typo, try again: ")
			continue
		else:
			break
	if warning == "N":
		sys.exit()
else:
	copy_str = os.path.split(expdir)[1] + "_distractors"
	copy_dir = os.path.join(expdir, copy_str)
	os.mkdir(copy_dir)# TODO create the copy location

# iterate over directories within expdir with a *.raw file in them
rawfile_glob_exp = os.path.join(os.path.normpath(args.expdir),
								"*",
								"*.raw"
								)

for rf in glob.glob(rawfile_glob_exp):
	parent = os.path.dirname(rf)
	acq = os.path.split(parent)[1]
	stimfile = os.path.join(parent,"word.txt")

	try:
		stim = read_stimfile(stimfile, deaccent=True)
	except FileNotFoundError:
		print("No alignment TG in {}; skipping".format(acq))
		continue

	if args.delete:
		if stim in distractor_list: 
			shutil.rmtree(parent)
	else:
		if stim in distractor_list:
			copy_path = os.path.join(copy_dir,acq)
			shutil.copytree(parent, copy_path)
			shutil.rmtree(parent)
