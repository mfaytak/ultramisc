import argparse
import os, re, sys, glob, shutil
from ultratils.rawreader import RawReader
import pandas as pd
from hashlib import sha1
from collections import OrderedDict
import audiolabel
import numpy as np
from operator import itemgetter
from ultramisc.utils.ebutils import read_echob_metadata

''' 
Script to cache vowel and nasal data of interest in Mandarin Chinese. Assumes
TextGrid annotations with phone set used in Montreal Forced Aligner for its
pre-trained Mandarin Chinese acoustic model.

Lists of target segments and/or can be input to selectively extract data. If
either list is omitted, no restrictions are 

Usage: python nasalcoda-cache-frames.py [expdir] [words] [segments] [--flop -f]
  expdir: directory containing all ultrasound acquisitions for a subject
  words: list of target words, plaintext
  segments: list of target segments, plaintext (including suprasegmentals)
  --flop: horizontally mirror the data (if probe was used backwards)
'''

def read_stimfile(stimfile):
	with open(stimfile, "r") as stfile:
		stim = stfile.read().rstrip('\n').upper()
	return stim

# read in command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing \
					acquisitions in flat structure"
					)
parser.add_argument("words",
					help="Plaintext list of target words to be extracted"
					)
parser.add_argument("segments",
					help="Plaintext list of target segments to be extracted"
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

frames_out = os.path.join(expdir,"frames.npy")
metadata_out = os.path.join(expdir,"frames_metadata.pickle")

# glob expression: locates .raw files in subdirs
rawfile_glob_exp = os.path.join(expdir,"*","*.raw")

# create regular expressions for target words and segments
# TODO: default to match ^(?!sil|sp).* for phones
# TODO: default to match "not nothing" for words 
with open(args.words, 'r') as mydict:
	wrds = [line.strip().split()[0].lower() for line in mydict.readlines()]
with open(args.segments,'r') as mysegm:
	segs = [line.strip().split()[0] for line in mysegm.readlines()]
	
# make a more generally useful regular expression for segments
# TODO set these to "any alphanumeric label which isn't sp or sil" if args
# aren't provided
word_regexp = re.compile("^({})$".format('|'.join(wrds)))
seg_regexp = re.compile("^({})$".format('|'.join(segs)))

# folder path for discards
disc = os.path.join(expdir,"_discards")

# empty data collection objects
data = None
recs = []

# loop through available .raw files
for rf in glob.glob(rawfile_glob_exp):
	parent = os.path.dirname(rf)
	acq = os.path.split(parent)[1]
	stimfile = os.path.join(parent,"stim.txt")
	stim = read_stimfile(stimfile)
	if stim == "BOLUS" or stim == "PRACTICE":
		continue
	print("Now working on " + acq)
	wav = os.path.join(parent,str(acq + ".ch1.wav"))
	tg = os.path.join(parent,str(acq + ".ch1.TextGrid"))
	sync = os.path.join(parent,str(acq + '.sync.txt'))
	sync_tg = os.path.join(parent,str(acq + ".sync.TextGrid"))
	idx_txt = os.path.join(parent,str(acq + ".idx.txt"))
	
	# instantiate RawReader, which extracts ultrasound data from .raw files
	if data is None:
		try:
			nscanlines, npoints, junk = read_echob_metadata(rf)
		except ValueError: 
			print("WARNING: no data in {}.img.txt".format(acq))
			nscanlines = int(input("\tnscanlines (usually 64) ")) # TODO update values
			npoints = int(input("\tnpoints (usually 1024) "))
			junk = int(input("\tjunk (usually 78) "))
	
	rdr = RawReader(rf, nscanlines=nscanlines, npoints=npoints)
	
	# instantiate LabelManager objects for FA transcript and sync pulses
	try: 
		pm = audiolabel.LabelManager(from_file=tg, from_type="praat")
	except FileNotFoundError:
		print("No alignment TG in {}; skipping".format(acq))
		continue
		
	try: 
		sync_pm = audiolabel.LabelManager(from_file=sync_tg, from_type="praat")
	except FileNotFoundError:
		print("No sync TG in {}; skipping".format(acq))
		continue
	
	for seg,match in pm.tier('phones').search(seg_regexp, return_match=True):
		context = pm.tier('words').label_at(seg.center).text
		if context in wrds:  
			before = pm.tier('phones').prev(seg)

			# assume default "sp" if there is no following label;
			# i.e. empty final interval
			after = pm.tier('phones').next(seg)
			try:
				after_label = after.text
			except AttributeError: 
				after_label = 'sp'
			two_after = pm.tier('phones').next(after)
			try:
				two_after_label = two_after.text
			except AttributeError: 
				two_after_label = 'sp'

			# match only the last two segments, sequence VN
			# if-else statement can be removed to make the script more general
			# (will return all instance of target phones in target words)
			if not (after_label == 'sp' or two_after_label == 'sp'):
				pass

			else:
				#print("Found {} in {} in {}".format(seg.text,context,acq))
				# separate suprasegmental numbers from seg.text
				match = re.match(r"([a-z]+)([0-9]+)", seg.text, re.I)
				if match:
					out_phone, out_sup = match.groups()
					#print(out_phone, out_sup)
				else:
					out_phone = seg.text
					out_sup = "NA"
					#print(out_phone, out_sup)
					
				# get midpoint time and find closest ultrasound frame in sync TG
				midpoint = seg.center
				diff_list = []
				diff2_list = []
				for frame in sync_pm.tier('pulse_idx'):
					diff = abs(frame.t1 - midpoint)
					diff_list.append(diff)
				for frame in sync_pm.tier('raw_data_idx'):
					diff2 = abs(frame.t1 - midpoint)
					diff2_list.append(diff2)
				# TODO rewrite this chunk, temporary fix added
				mid_pulse_idx_num = min(enumerate(diff_list), key=itemgetter(1))[0] 
				mid_raw_data_idx_num = min(enumerate(diff2_list), key=itemgetter(1))[0]
				
				# get midpoint frame; discard if out of recorded range
				try:
					raw = rdr.get_frame(mid_pulse_idx_num - 1) # temporary fix
				except IndexError: # thrown by RawReader.rdr if no frame at timepoint
					# issue warning and move entire acq to discards folder
					print("No frame available in {}, discarding".format(acq))
					rdr.close()
					if not os.path.isdir(disc):
						os.mkdir(disc)
					shutil.copytree(parent, os.path.join(disc,acq))
					shutil.rmtree(parent)
					continue

				trim = raw[junk:,:]

				# flop if needed
				if args.flop:
					trim = np.fliplr(trim)
				
				if data is None:
					data = np.expand_dims(trim, axis=0)
				else:
					data = np.concatenate([data, np.expand_dims(trim, axis=0)])
					
				recs.append(
					OrderedDict([
						('speaker', expdir),
						('timestamp', acq),
						('time', midpoint),
						('pulseidx', int(mid_pulse_idx_num)),
						('width', nscanlines),
						('height', npoints - junk),
						('phone', out_phone),
						('sup', out_sup),
						('stim', stim),
						('before', re.sub(r'[0-9]+', '', before.text)),
						('after', re.sub(r'[0-9]+', '', after.text)),
						('sha1', sha1(trim.ravel()).hexdigest()),
						('sha1_dtype', trim.dtype)
					])
				)
			
md = pd.DataFrame.from_records(recs, columns=recs[0].keys())

# check that metadata matches data, frame-by-frame
assert(len(md) == data.shape[0])
for idx,row in md.iterrows():
	assert(row['sha1'] == sha1(data[idx].ravel()).hexdigest())

np.save(frames_out, data)
md.to_pickle(metadata_out)