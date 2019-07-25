'''
process-cache.py: a python command line utility for cleaning up
  ultrasound frame data stored in a .npy cache. A metadata
  pickle is used to identify frames. Both of these files are
  created using one of the *-cache-frames.py scripts also stored 
  in this repository.

  To be more precise, this script fan-converts, optionally 
  flops (horizontally flips) the converted data, and applies 
  filtering operations for speckle reduction and edge enhancement.
  One run of the script can be applied to multiple speakers' data
  sets. A speaker-specific ROI mask is applied to each data set.

Usage: python process-cache.py [expdir] [--flop -f]
  expdir: The experiment directory, which contains a folder for
          each subject. These in turn contain files called 
          frames.npy and frames_metadata.pickle.
  --flop: If used, horizontally mirror the data (to correct for 
  		  ultrasound probe being oriented backwards).
'''

import argparse
import glob
import matplotlib.pyplot as plt
import numpy as np 
import os
import pandas as pd
import re
import sys

from hashlib import sha1
from imgphon import ultrasound as us
from ultratils.pysonix.scanconvert import Converter

# read in arguments from command line
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing all subjects'\
						  caches and metadata in separate folders"
					)
parser.add_argument("-o", 
					"--overwrite", 
					help="Overwrites existing outputs if present.",
					action="store_true"
					)
parser.add_argument("-f", 
					"--flop", 
					help="Horizontally flip the data", 
					action="store_true"
					)
args = parser.parse_args()

# create some objects we will need to instantiate the converter
class Header(object):
	def __init__(self):
		pass
class Probe(object):
	def __init__(self):
		pass
# to be defined below on first pass through data
conv = None

# argument checking
try:
	expdir = args.expdir
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

# create some output file handles
frames_out = "frames_proc.npy"
metadata_out = "frames_proc_metadata.pickle"

# loop through 
for root,directories,files in os.walk(expdir):
	for d in directories:

		if os.path.exists(os.path.join(root,d,frames_out)):
			if args.overwrite:
				print("Skipping {}, already processed".format(d))
				pass
			else:
				continue

		# folder name without any alphabetic characters
		subject = re.sub("[^0-9]","",d)

		# read in data and metadata
		data_in = os.path.join(root,d,"frames.npy")
		pca_data = np.load(data_in)
		metadata_in = os.path.join(root,d,'frames_metadata.pickle')
		pca_md = pd.read_pickle(metadata_in)

		# check that metadata matches data, frame-by-frame
		assert(len(pca_md) == pca_data.shape[0])
		for idx,row in pca_md.iterrows():
			assert(row['sha1'] == sha1(pca_data[idx].ravel()).hexdigest())

		# TODO implement a general data subsetter (external lists)

		# define Converter parameters from first acq for first subj
		if conv is None:
			print("Defining Converter ...")
			header = Header()
			header.w = pca_data[0].shape[1]   # input image width
			header.h = pca_data[0].shape[0]   # input image height, trimmed
			header.sf = 4000000         	# magic number, sorry!
			probe = Probe()
			probe.radius = 10000        	# based on '10' in transducer model number
			probe.numElements = 128     	# based on '128' in transducer model number
			probe.pitch = 185           	# based on Ultrasonix C9-5/10 transducer
			conv = Converter(header, probe)

		print("Defining region of interest ...")

		# get mean frame and apply mask
		mean_frame = pca_data.mean(axis=0)
		conv_mean = np.flipud(conv.convert(np.flipud(mean_frame)))
		plt.title("Mean frame, Spkr {:}".format(subject))
		plt.imshow(conv_mean, cmap="Greys_r")
		file_ending_mean = "subj{:}_mean.pdf".format(subject)
		savepath_mean = os.path.join(root,d,file_ending_mean)
		plt.savefig(savepath_mean)
		roi_upper = 600
		roi_lower = 200
		roi_left = 20
		roi_right = 50

		# show user the masked data and ask for input on mask
		while True:
			mask = us.roi(mean_frame, 
				upper=roi_upper, 
				lower=roi_lower,
				left=roi_left,
				right=roi_right)
			masked_mean = mean_frame * mask
			conv_masked = np.flipud(conv.convert(np.flipud(masked_mean)))
			plt.title("Mean frame and RoI, Spkr {:}".format(subject))
			plt.imshow(conv_masked, cmap="Greys_r")
			file_ending_roi = "subj{:}_roi.pdf".format(subject)
			savepath_roi = os.path.join(root,d,file_ending_roi)
			plt.savefig(savepath_roi)
			good_roi = input("Inspect {:}. Good RoI? (Y/N) ".format(savepath_roi))

			# If good, go ahead. If not, ask for new bounds.
			if good_roi.upper() in ['Y', 'N']:
				if good_roi.upper() == "Y":
					break
				else:
					roi_upper = int(input("Please provide a new upper bound for RoI (currently {:}): ".format(roi_upper)))
					roi_lower = int(input("Please provide a new lower bound for RoI (currently {:}): ".format(roi_lower)))
					roi_left = int(input("Please provide a new left bound for RoI (currently {:}): ".format(roi_left)))
					roi_right = int(input("Please provide a new right bound for RoI (currently {:}): ".format(roi_right)))
			else:
				print("Typo, try again ...")

		# some filtering parameters based on image size
		conv_frame = conv.convert(pca_data[0])
		adj_radius = int(conv_frame.shape[0]/50) # for median filter

		# heads-up
		print("Preprocessing data for PCA ...")

		# make a sample frame for reference and show user
		in_sample = pca_data[0]
		masked_samp = in_sample * mask # using mask defined above
		sradd_samp = us.srad(masked_samp)
		convd_samp = np.flipud(conv.convert(np.flipud(sradd_samp)))
		clean_samp = us.clean_frame(convd_samp, median_radius=adj_radius)
		rescaled_samp = clean_samp * 255
		sample_frame = rescaled_samp.astype(np.uint8)
		plt.title("Sample frame, Spkr {:}".format(subject))
		plt.imshow(sample_frame, cmap="Greys_r")
		file_ending_sample = "subj{:}_sample.pdf".format(subject)
		savepath_sample = os.path.join(root,d,file_ending_sample)
		plt.savefig(savepath_sample)
		print("Please check sample frame at {}!".format(savepath_sample))

		# set up ultrasound frame array for PCA
		out_frames = np.empty([pca_data.shape[0]] + list(conv_frame.shape)) * np.nan
		out_frames = out_frames.astype('uint8')
		filt_hds = []
		total = out_frames.shape[0]

		for idx,frame in enumerate(pca_data):
			masked = frame * mask # using mask defined above
			sradd = us.srad(masked)
			convd = np.flipud(conv.convert(np.flipud(sradd)))
			clean = us.clean_frame(convd, median_radius=adj_radius)
			# copying to out_frames casts to np.uint8; rescaling required
			rescaled = clean * 255
			out_frames[idx,:,:] = rescaled
			# new sha1 hex: filtered, conv to np.uint8
			filt_hds.append(sha1(out_frames[idx].ravel()).hexdigest()) 
			print("\tAdded frame {} of {}".format(idx+1,total))

		# add new sha1 hash as a column in the df
		pca_md = pca_md.assign(sha1_filt=pd.Series(filt_hds, index=pca_md.index))

		# check that metadata matches data, frame-by-frame
		assert(len(pca_md) == pca_data.shape[0])
		for idx,row in pca_md.iterrows():
			assert(row['sha1'] == sha1(pca_data[idx].ravel()).hexdigest())

		# output
		np.save(os.path.join(root,d,frames_out), out_frames)
		pca_md.to_pickle(os.path.join(root,d,metadata_out))
