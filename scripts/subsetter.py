#!/usr/bin/env python

# subsetter.py: pick out a subset of acquisitions in an experiment directory.
# usage: python subsetter.py 

# TODO test both options (delete, not delete)

import os, sys, glob, shutil
import argparse

def read_stimfile(stimfile):
	with open(stimfile, "r") as stfile:
		stim = stfile.read().rstrip('\n')
	return stim

# parse argument(s)
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
parser.add_argument("-d",
					"--delete", 
					help="Delete non-target files in place \
						(default behavior is to copy target \
						files to new location)",
					action="store_true"
					)
args = parser.parse_args()

expdir = os.path.normpath(args.expdir)

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
	copy_str = os.path.split(expdir)[1] + "_copy"
	copy_dir = os.path.join(expdir, copy_str)
	os.mkdir(copy_dir)# TODO create the copy location

# desired analysis set; change as required
target_list = ["FUH", "BUH", "FUW", "BUW", "BAAE", "BIY"]

# iterate over directories within expdir with a *.raw file in them
rawfile_glob_exp = os.path.join(os.path.normpath(args.expdir),
								"*",
								"*.raw"
								)

for rf in glob.glob(rawfile_glob_exp):
	parent = os.path.dirname(rf)
	acq = os.path.split(parent)[1]
	stimfile = os.path.join(parent,"stim.txt")
	stim = read_stimfile(stimfile)
	if args.delete:
		if stim not in target_list: 
			shutil.rmtree(parent)
	else:
		if stim in target_list:
			copy_path = os.path.join(copy_dir,acq)
			shutil.copytree(parent, copy_path)
