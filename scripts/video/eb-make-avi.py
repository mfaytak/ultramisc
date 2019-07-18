#!/usr/bin/env python

# eb-extract-all.py: extract all frames as BMPs from a raw file
# WARNING: largely superseded by code in ./flap-video-writer.py
# usage: python eb-extract-all.py expdir (-f / --flop)

# TODO this shares a lot of structure in common with eb-extract-frames.py
# pull out functions?

import os, re, glob, shutil
from PIL import Image
import numpy as np
import argparse
import audiolabel
from operator import itemgetter
from ultratils.rawreader import RawReader
from ultratils.pysonix.scanconvert import Converter
import subprocess

def read_stimfile(stimfile):
    with open(stimfile, "r") as stfile:
        stim = stfile.read().rstrip('\n')
    return stim

def read_echob_metadata(rawfile):
    '''
    Gather information about a .raw file from its .img.txt file. 
    '''
    mfile = os.path.splitext(rawfile)[0] + ".img.txt"
    mdict = {}
    with open(mfile, 'r') as mf:
        k = mf.readline().strip().split("\t")
        v = mf.readline().strip().split("\t")
        for fld,val in zip(k, v):
            mdict[fld] = int(val)
    
    nscanlines = mdict['Height']
    npoints = mdict['Pitch']
    junk = npoints - mdict['Width'] # number of rows of junk data at outer edge of array
    
    return nscanlines, npoints, junk

class Header(object):
    def __init__(self):
        pass
class Probe(object):
    def __init__(self):
        pass

# empty RawReader and Converter handles
rdr = None
conv = None

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
	sync = os.path.join(parent,str(basename + '.sync.txt'))
	idx_txt = os.path.join(parent,str(basename + ".idx.txt"))

	# make destination and copy "support" files for parent file 
	copy_dir = os.path.join(output_dir,basename)

	os.mkdir(copy_dir)
	shutil.copy(wav, copy_dir)
	shutil.copy(idx_txt, copy_dir)
	shutil.copy(stimfile, copy_dir)

	# get frame indices
	frame_indices = []
	with open(idx_txt, "r") as it:
		for line in it:
			frame_indices.append(int(line.strip()))

	start_extr = frame_indices[0]
	end_extr = frame_indices[-1]

	# extract and convert v.t1 - v.t2 range
	for idx in range(start_extr, (end_extr)):

		# extract frame using RawReader
		unconv_frame = rdr.get_frame(idx)

		# trim junk pixels off of top
		trimmed_frame = unconv_frame[junk:,:]
		if args.flop:
			trimmed_frame = np.fliplr(trimmed_frame)

		# convert to fan shape
		conv_frame = conv.convert(np.flipud(trimmed_frame))
		ready_frame = np.flipud(conv_frame)

		# create frame handle and save to copy dir
		fh = basename + "." + "{0:05d}".format(idx) + ".bmp"
		out_img = Image.fromarray(ready_frame)
		out_img.save(os.path.join(copy_dir,fh))

	frame_exp = os.path.join(copy_dir, basename + ".%05d.bmp")
	print(frame_exp)
	framerate = 25 # TODO tweak/automatically get
	out_fh = basename + '.avi'
	out_path = os.path.join(copy_dir, out_fh)
	avi_args = ['ffmpeg', '-y',
					'-i', frame_exp,
					'-framerate', str(framerate),
					'-vcodec', 'huffyuv',
					out_path]
	subprocess.check_call(avi_args)