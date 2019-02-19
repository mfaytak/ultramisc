#!/usr/bin/env python

# TODO RENAME extract frame BMPs for contour extraction
# from ultrasonix data, using ultratils.exp.Exp class
# This is set up to extract Kejom vowel and fricative data
# usage: python ulx-extract-frames.py expdir (-f / --flop)


import os, re, shutil
from PIL import Image
from ultratils.exp import Exp
import numpy as np
import argparse
import audiolabel

# set of segments being searched for
vre = re.compile(
		"^(SH|IY1|UW1|IH1|UH1|AA1)"
		)

skip_word_list = ["GAA","LAA","FAA","FIY"]

parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
parser.add_argument("-s", "--skip", 
					help="Skip an acquisition if it already has BMP files",
					action="store_true"
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
output_dir = os.path.join(expdir,"_frames")
try:
	os.mkdir(output_dir)
except FileExistsError:
	shutil.rmtree(output_dir)
	os.mkdir(output_dir)

e = Exp(expdir=expdir)   # from command line args
e.gather()

# error logging
mid_skip_count = 0
slice_skip_count = 0
sync_skip_count = 0
window_skip_count = 0

err_log = os.path.join(expdir,"_errors.txt")
head = "\t".join(["acq","problemType"])

with open(err_log, "w") as out:
	out.write(head)

	for a in e.acquisitions:

		patchy = False

		# check for sync.txt; skip if one doesn't exist
		try:
			a.sync_lm
		except IOError:
			print("SKIPPING: no synchronization for {:}.".format(a.timestamp))
			sync_skip_count += 1
			out.write("\t".join([a.timestamp,"sync"])+"\n")
			continue

		# TODO check
		basename = a.timestamp

		copy_dir = os.path.join(output_dir,basename)

		try:
			os.mkdir(copy_dir)
		except FileExistsError:
			# TODO check if the new stimulus is "IH" or "UH"
				# if true - then make a separate dir for SH?
				#  need a more general solution for this problem, both here
				#  and in the echob script.
			print("WARNING: Multiple targets in {}".format(basename))
			print("\t Previous repetition overwritten")
			shutil.rmtree(copy_dir)
			os.mkdir(copy_dir)

		# move key files over to new dir
		try:
			shutil.copy(a.abs_sync_tg, copy_dir)
		except IOError:
			print("SKIPPING: Incomplete synchronization for {:}.".format(a.timestamp))
			sync_skip_count += 1
			out.write("\t".join([a.timestamp,"sync"])+"\n")
			continue
		tg = str(a.abs_image_file + ".ch1.TextGrid")
		shutil.copy(tg, copy_dir)
		sync_txt = str(a.abs_image_file + ".sync.txt")
		shutil.copy(sync_txt, copy_dir)
		shutil.copy(a.abs_stim_file, copy_dir)
		shutil.copy(os.path.splitext(a.abs_audio_file)[0]+".ch1.wav", copy_dir)
		
		# instantiate LabelManager
		pm = audiolabel.LabelManager(from_file=tg, from_type="praat")

		# get recording window times
		start_window = a.pulse_idx.search(r'\w')[0].t1
		end_window = a.pulse_idx.search(r'\w')[-1].t2

		# for each segment in vre detected in file:
		for v,m in pm.tier('phone').search(vre, return_match=True):
			word = pm.tier('word').label_at(v.center).text
			if word in skip_word_list:
				continue

			if v.t1 < start_window or v.t2 > end_window:
				print("SKIPPING: part of segment is outside recording window in {:}".format(a.timestamp))
				window_skip_count += 1
				out.write("\t".join([a.timestamp,"window"])+"\n")
				continue

			# check for more than 1 consecutive NA in a row in the interval of interest
			for c in a.raw_data_idx.tslice(t1=v.t1,t2=v.t2): 
				if c.text == "NA":
					if a.raw_data_idx.prev(c).text == "NA":
						print("SKIPPING: {:} is patchy, consec. NA frames".format(a.timestamp))
						slice_skip_count += 1
						out.write("\t".join([a.timestamp,"slice"])+"\n")
						patchy = True
						break

			if patchy:
				continue

			# if still good, work over each file's "slices" and get all frames in that range
			for l in a.pulse_idx.tslice(t1=v.t1,t2=v.t2):
				d_tuple = a.frame_at(l.center,convert=True)
				d_array = d_tuple[0]

				# if frame is blank (text is "NA"), grab previous frame
				if d_array is None:
					prevl = a.pulse_idx.prev(l) 
					d_tuple = a.frame_at(prevl.center,convert=True) 
					d_array = d_tuple[0]

				d = d_array.astype(np.uint8)
				d = np.flipud(d)

				# flip left-right ("flop") if backwards 
				if args.flop:
					d = np.fliplr(d)

				frame = Image.fromarray(d)
				imgname = '{:}.{:}.bmp'.format(a.timestamp, l.text)
				frame.save(os.path.join(copy_dir, imgname)) 
