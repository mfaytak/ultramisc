#!/usr/bin/env python

# eb-extract-frames.py: extract frame BMPs for contour extraction
# usage: python eb-extract-frames.py expdir (-f / --flop)


import os, re, sys, glob, shutil
from PIL import Image
import numpy as np
import argparse
from operator import itemgetter
import pandas as pd
from hashlib import sha1
from collections import OrderedDict
import audiolabel
import imgphon as iph
from ultratils.rawreader import RawReader
#from ultratils.pysonix.scanconvert import Converter

def read_stimfile(stimfile):
	with open(stimfile, "r") as stfile:
		stim = stfile.read().rstrip('\n')
	return stim

# TODO move this (and the other fcns?) to utils
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

# a list of targets from dict.local, to be updated as required.
target_list = ['IZ', 'BIZX', 'SIZ', 'XIZ', 
			   'IY', 'BIY', 'SIY', 'XIY',
			   'YZ', 'XYZ',
			   'EU', 'NYEU', 'XEU', 
			   'SEI', 
			   'AAE', 'BAAE', 'SAAE', 'XAE', 
			   'UW', 'BUW', 'SUW', 'XUEQ',
			   'OOW', 'BOOW', 'SOOW', 'FOOW',
			   # 'AHR', 'HAAR', 'NIZ', 'NIY', 'AAW', # excluding 儿 for time being
			   'SIEX', 'XIEX',
			   'SZ', 'SZW',
			   'BUH', 'BOQ', 'FUH', 'FUW']

iz_list = ['IZ', 'BIZX', 'SIZ', 'XIZ']

recs = [] # metadata store
data = None # array that will contain ultrasound data
#frame_dim_1 = None
#frame_dim_2 = None

# TODO set of segments being searched for
vre = re.compile(
		 "^(IY1|IH1|UH1|UW1|OW1|AE1|SH|S)$" 
	)

# distance (in frames) away from intended time point that can be subbed in
threshhold = 3

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

# check for appropriate directory
try:
	expdir = args.expdir
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

# set up copy location
output_dir = os.path.join(expdir,"_copy")
try:
	os.mkdir(output_dir)
except FileExistsError:
	shutil.rmtree(output_dir)
	os.mkdir(output_dir)

logfile = os.path.join(expdir,"frames_log.txt")
discard_folder = os.path.join(expdir,"discards")
frames_out = os.path.join(expdir,"frames.npy")
metadata_out = os.path.join(expdir,"frames_metadata.pickle")

with open(logfile,"w") as header:
	header.write("acq"+"\t"+"stim"+"\t"+"phone"+"\t"+"status"+"\t"+"problem"+"\n")

# glob expression
rawfile_glob_exp = os.path.join(expdir,"*","*.raw")

for rf in glob.glob(rawfile_glob_exp):

	parent = os.path.dirname(rf)
	acq = os.path.split(parent)[1]

	# use stim.txt to skip non-trials
	stimfile = os.path.join(parent,"stim.txt")
	stim = read_stimfile(stimfile)
	if stim == "bolus" or stim == "practice":
		continue

	print("Found "+acq)
	# define "support" file names based on .raw
	wav = os.path.join(parent,str(acq + ".ch1.wav"))
	tg = os.path.join(parent,str(acq + ".ch1.TextGrid"))
	sync = os.path.join(parent,str(acq + '.sync.txt'))
	sync_tg = os.path.join(parent,str(acq + ".sync.TextGrid"))
	idx_txt = os.path.join(parent,str(acq + ".idx.txt"))

	# set up RawReader and frame dimensions
	if data is None:
		try:
			nscanlines, npoints, junk = read_echob_metadata(rf)
		except ValueError: 
			print("WARNING: no data in {}.img.txt, please input:".format(acq))
			nscanlines = int(input("\tnscanlines (usually 127) "))
			npoints = int(input("\tnpoints (usually 1020) "))
			junk = int(input("\tjunk (usually 36, or 1020 - 984) "))
		#frame_dim_1 = nscanlines
		#frame_dim_2 = npoints - junk

	rdr = RawReader(rf, nscanlines=nscanlines, npoints=npoints)

	# instantiate LabelManagers
	pm = audiolabel.LabelManager(from_file=tg, from_type="praat")
	sync_pm = audiolabel.LabelManager(from_file=sync_tg, from_type="praat")

	# extract ndarray representations of frames from .raw file
	for v,m in pm.tier('phone').search(vre, return_match=True):
		pron = pm.tier('word').label_at(v.center).text

		# skip any tokens from non-target words
		if pron not in target_list:
			continue

		# get phone label, disambiguating IY and IH based on pronunciation
		# skip some IY (diphthongized variants in some words)
		if v.text == "IY1":
			if pron in iz_list: # change if IZ
				phone = "IZ1"
			elif pron == "YZ" or pron == "XYZ":
				phone = "YZ1"
			elif pron == "SIEX" or pron == "XIEX":
				continue
			else:
				phone = v.text
		elif v.text == "IH1":
			if pron == "SZ":
				phone = "ZZ1"
			elif pron == "SZW":
				phone = "ZW1"
			elif pron == "EU" or pron == "XEU":
				phone = "YY1"
		else:
			phone = v.text

		# TODO make this a bit more extensible; test
		before = pm.tier('phone').prev(v).text 
		if before == "sp":
			before = pm.tier('phone').prev(v,skip=1).text
		after = pm.tier('phone').next(v).text 
		if after == "sp":
			after = pm.tier('phone').next(v,skip=1).text

	   # get midpoint time and find closest ultrasound frame in sync TG
		# TODO more efficient to duplicate ultratils frame_at approach
		mid_timepoint = v.center
		diff_list = []
		diff2_list = []
		for frame in sync_pm.tier('pulse_idx'):
			diff = abs(frame.t1 - mid_timepoint)
			diff_list.append(diff)
		for frame in sync_pm.tier('raw_data_idx'):
			diff2 = abs(frame.t1 - mid_timepoint)
			diff2_list.append(diff2)
		mid_pulse_idx_num = min(enumerate(diff_list), key=itemgetter(1))[0] 
		mid_raw_data_idx_num = min(enumerate(diff2_list), key=itemgetter(1))[0] 

		# get frame, and check for NaN frames
		change = 0
		discard_acq = False
		while True:
			pre_rawdata = rdr.get_frame(mid_pulse_idx_num)
			if pre_rawdata is None:
				mid_pulse_idx_num -= 1
				mid_raw_data_idx_num -= 1 # TODO: necessary?
				change += 1
				if change > threshhold:
					with open(logfile, "a") as log:
						log.write(acq+"\t"+stim+"\t"+phone+"\t"+"discarded"+"\t"+"passed threshhold")
					print("Frame change threshhold passed; acq {} discarded".format(acq))
					discard_acq = True
					break
				else:
					pass
			else:
				if change > 0:
					with open(logfile, "a") as log:
						log.write(acq+"\t"+stim+"\t"+phone+"\t"+"changed by {:}".format(change)+"\t"+"N/A")
					print("Changed target in {:} by".format(acq), change, "frames")
				break

		# discard the acquisition if needed
		if discard_acq:
			shutil.copytree(parent, os.path.join(discard_folder,acq))
			shutil.rmtree(parent)
			continue 

		# preprocessing of images
		rawdata = pre_rawdata.astype(np.uint8)
		trim_data = rawdata[junk:,:]

		if args.flop:
				trim_data = np.fliplr(trim_data)

		if data is None:
			data = np.expand_dims(trim_data, axis=0)
		else:
			data = np.concatenate([data, np.expand_dims(trim_data, axis=0)])

		# generate metadata row for current acq
		# TODO check variable names
		recs.append(
			OrderedDict([
				('timestamp', acq),
				('time', v.center),
				('pulseidx', int(mid_pulse_idx_num)),
				('rawdataidx', int(mid_raw_data_idx_num)),
				('width', nscanlines),
				('height', npoints - junk),
				('phone', phone),
				('stim', stim),
				('pron', pron),
				('before', before),
				('after', after),
				('sha1', sha1(trim_data.ravel()).hexdigest()),
				('sha1_dtype', trim_data.dtype)
			])
		)

md = pd.DataFrame.from_records(recs, columns=recs[0].keys())

# make sure there is one metadata row for each image frame
assert(len(md) == data.shape[0])

# compare checksums
assert(md.loc[0, 'sha1'] == sha1(data[0].ravel()).hexdigest())
assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1].ravel()).hexdigest())

np.save(frames_out, data)
md.to_pickle(metadata_out)