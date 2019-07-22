#!/usr/bin/env python

# eb-extract-frames.py: extract frame BMPs for contour extraction
# usage: python eb-extract-frames.py expdir (-f / --flop)

import argparse
import audiolabel
import glob
import numpy as np
import os
import re
import shutil

from operator import itemgetter
from PIL import Image
from ultratils.rawreader import RawReader
from ultratils.pysonix.scanconvert import Converter

from ultramisc.ebutils import read_echob_metadata, read_stimfile

class Header(object):
    def __init__(self):
        pass
class Probe(object):
    def __init__(self):
        pass

# empty RawReader and Converter handles
rdr = None
conv = None

# set of segments being searched for
vow = re.compile("^(UW1|OW1|UH1|AE1|IY1)")

parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
parser.add_argument("-f", 
					"--flop", 
					help="Horizontally flip the data", 
					action="store_true"
					)
args = parser.parse_args()

# read in expdir
expdir = os.path.normpath(args.expdir)

# set up copy location
output_dir = os.path.join(expdir,"_copy")
try:
	os.mkdir(output_dir)
except FileExistsError:
	shutil.rmtree(output_dir)
	os.mkdir(output_dir)

# glob expression
rawfile_glob_exp = os.path.join(expdir,"*","*.raw")

# loop through acqs and:
for rf in glob.glob(rawfile_glob_exp):

	parent = os.path.dirname(rf)
	basename = os.path.split(parent)[1]

	# use stim.txt to skip non-trials
	stimfile = os.path.join(parent,"stim.txt")
	stim = read_stimfile(stimfile)
	if stim == "bolus" or stim == "practice":
		continue

	# define RawReader and Converter parameters from first acq
	if conv is None:
		print("Defining Converter ...")
		# get image size data; allow for manual input if problems
		try:
			nscanlines, npoints, junk = read_echob_metadata(rf)
		except ValueError: 
			print("WARNING: no data in {}.img.txt, please input:".format(basename))
			nscanlines = int(input("\tnscanlines (usually 127) "))
			npoints = int(input("\tnpoints (usually 1020) "))
			junk = int(input("\tjunk (usually 36, or 1020 - 984) "))

		# TODO use metadata instead of hard-coded values
		header = Header()
		header.w = nscanlines       # input image width
		header.h = npoints - junk   # input image height, trimmed
		header.sf = 4000000         # magic number, sorry!
		probe = Probe()
		probe.radius = 10000        # based on '10' in transducer model number
		probe.numElements = 128     # based on '128' in transducer model number
		probe.pitch = 185           # based on Ultrasonix C9-5/10 transducer
		conv = Converter(header, probe)

	rdr = RawReader(rf, nscanlines=nscanlines, npoints=npoints)

	# define "support" file names based on .raw
	wav = os.path.join(parent,str(basename + ".ch1.wav"))
	tg = os.path.join(parent,str(basename + ".ch1.TextGrid"))
	sync = os.path.join(parent,str(basename + '.sync.txt'))
	sync_tg = os.path.join(parent,str(basename + ".sync.TextGrid"))
	idx_txt = os.path.join(parent,str(basename + ".idx.txt"))

	# instantiate LabelManager
	pm = audiolabel.LabelManager(from_file=tg, from_type="praat")

	# read in .sync.txt file and get recording window times
	sync = os.path.join(parent,str(basename + '.sync.txt'))
	sync_times = []
	with open(sync, 'r') as s:
		for line in s:
			try:
				sync_times.append(float(line.strip().split("\t")[0]))
			except ValueError:
				pass # ignore line if a header is present 
	rec_start = sync_times[0]
	rec_end = sync_times[-1]

	# extract frame(s) from .raw file
	# TODO handle multiple repititions by only taking last rep
	for v,m in pm.tier('phone').search(vow, return_match=True):
		pron = pm.tier('word').label_at(v.center).text

		# skip any tokens from non-target words
		if pron not in ["BUH", "FUH", "BUW", "BOOW", "BAAE", "BIY"]:
			continue
		# correct UH1 vowel depending on pronunciation FUH or BUH
		elif pron == "FUH":
			phone = "VU"
		elif pron == "BUH":
			phone = "BU"
		elif pron == "BOOW":
			phone = "UW"
		else:
			phone = v.text.replace('1','')

		# check segment start or end times: in recording window?
		if v.t1 < rec_start or v.t2 > rec_end:
			print("SKIPPED {:}, {:} outside recording window".format(basename, v.text))
			continue

		print("{} - found {} in {}".format(basename, phone, pron))

		# make destination and copy "support" files for parent file 
		copy_dir = os.path.join(output_dir,basename)
		# this will throw a warning if the directory is overwritten
		# by a second repetition of a target word in the file.
		# TODO put some more information in this?
		try:
			os.mkdir(copy_dir)
		except FileExistsError:
			print("WARNING: Multiple targets in {}".format(basename))
			print("\t Previous repetition overwritten")
			shutil.rmtree(copy_dir)
			os.mkdir(copy_dir)
		shutil.copy(wav, copy_dir)
		shutil.copy(tg, copy_dir)
		shutil.copy(sync_tg, copy_dir)
		shutil.copy(idx_txt, copy_dir)
		shutil.copy(stimfile, copy_dir)
		shutil.copy(sync, copy_dir)

		# get segmental context (non-silence)
		skip_back = 0
		while True:
			if skip_back == 0:
				before = pm.tier('phone').prev(v).text
			else:
				before = pm.tier('phone').prev(v,skip=skip_back).text
			if before == "sp":
				skip_back += 1
			else:
				break

		skip_ahead = 0
		while True:
			if skip_ahead == 0:
				after = pm.tier('phone').prev(v).text
			else:
				after = pm.tier('phone').prev(v,skip=skip_ahead).text
			if after == "sp":
				skip_ahead += 1
			else:
				break

		# TODO store phone, before, after
		# TODO move these to format-con? you'll actually need them then

		# find frame idx of v.t1 - v.t2 range and of midpoint
		t1_diff = [abs(v.t1 - t) for t in sync_times]
		t2_diff = [abs(v.t2 - t) for t in sync_times]
		tmid_diff = [abs(v.center) - t for t in sync_times]
		t1_match = min(enumerate(t1_diff), key=itemgetter(1))[0]
		t2_match = min(enumerate(t2_diff), key=itemgetter(1))[0]
		tmid_match = min(enumerate(tmid_diff), key=itemgetter(1))[0]

		# extract and convert v.t1 - v.t2 range
		for idx in range(t1_match, (t2_match+1)):

			# extract frame using RawReader
			unconv_frame = rdr.get_frame(idx)

			# trim junk pixels off of top
			trimmed_frame = unconv_frame[junk:,:]
			if args.flop:
				trimmed_frame = np.fliplr(trimmed_frame)

			# TODO filter?

			# convert to fan shape
			conv_frame = conv.convert(np.flipud(trimmed_frame))
			ready_frame = np.flipud(conv_frame)

			# create frame handle and save to copy dir
			fh = basename + "." + str(idx) + ".bmp"
			out_img = Image.fromarray(ready_frame)
			out_img.save(os.path.join(copy_dir,fh))
