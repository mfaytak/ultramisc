#!/usr/bin/env python

# subsetter.py: pick out a subset of acquisitions in an experiment directory.
# usage: python subsetter.py expdir

import os, sys, glob, shutil
import argparse
from ultratils.exp import Exp 

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
	copy_str = os.path.split(expdir)[1] + "_subset"
	copy_dir = os.path.join(expdir,copy_str)
	try:
		os.mkdir(copy_dir)
	except FileExistsError:
		shutil.rmtree(copy_dir)
		os.mkdir(copy_dir)

# desired analysis set; change as required
target_list = ["EBA'", "BV", "EBVUH", "BUW", "BIY", "SHIY", "SHUH", "ESHIH", "GHUH", "KIH", "KUH", "KUW", "KIY"] # last four for ACAL
# differences among all four "elsewhere" high vowels in same frame: 
# no IH??
# /a/ TA', SA', FA', KA', GHA'; /i/ EFIY, BIY, SIY, KIY, ETIY; /i/ postalveolar ACHIY; 
# /u/ ZHUW, EFUW, BUW, TUW; /1/ EGHIH, CHIH; /0/ GHUH, NYUH; /0/ postalveolar CHUH;
# /0/ labiodental PFUH, EFUH; misc. ETYI, EFYI, BYI', TYI', FYI', KYI', CHI', ETYIH, BYI, BYIH

e = Exp(expdir=expdir)   # from command line args
e.gather()

for a in e.acquisitions:

	stim = read_stimfile(a.abs_stim_file)
	parent = os.path.dirname(a.abs_stim_file)

	if args.delete:
		if stim not in target_list: 
			shutil.rmtree(parent)
	else:
		if stim in target_list:
			copy_path = os.path.join(copy_dir,a.timestamp)
			shutil.copytree(parent, copy_path)
