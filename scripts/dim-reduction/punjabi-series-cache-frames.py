#!/usr/bin/env python

"""
TODO docstring
"""

from __future__ import absolute_import, division, print_function

import os, sys, glob, re
from PIL import Image
import struct
import argparse
from operator import itemgetter
import numpy as np
from scipy import ndimage
import subprocess
import pandas as pd
from hashlib import sha1
from collections import OrderedDict

# read in args
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
args = parser.parse_args()

# check for appropriate directory
expdir = args.directory
try:
    assert os.path.exists(args.directory)
except AssertionError:
    # TODO raise exception
    print("\tDirectory provided doesn't exist")
    parser.print_help()
    sys.exit(2)

data = None
recs = []
frames_out = os.path.join(expdir,"frames.npy")
metadata_out = os.path.join(expdir,"frames_metadata.pickle")
png_glob_exp = os.path.join(os.path.normpath(expdir),"*","*","*.png")

# for filename in list-of-files:
for frame in glob.glob(png_glob_exp): 

	# will get subject, word, token, etc out of four-level nested dir
	# that seems to be typical of AAA output
	name = os.path.split(frame)[1]
	basename = os.path.splitext(name)[0]
	idx = basename.split('_')[-1]
	subj, word, token = os.path.dirname(frame).split('/')
	print(subj, word, token, basename, idx)

	# get ndarray from image file. issue is probably here. Unconverted RGB:
	inframe = np.asarray(Image.open(frame)) 
	# converted from RGB to grayscale (one-channel):
	inframe = np.asarray(Image.open(frame).convert("L")) 
	# converted to uint8:
	rawdata = inframe.astype(np.uint8)

	recs.append(
		OrderedDict([
			('filename', basename), 
			('subject', subj),
			('stim', word),
			('token', token),
			('index', idx),
			('sha1', sha1(rawdata.ravel()).hexdigest()), # tuple error is thrown here.
			('sha1_dtype', rawdata.dtype)
		])
	)

	# add frame ndarray to frames list
	if data is None:
		data = np.expand_dims(rawdata, axis=0)
	else:
		data = np.concatenate([data, np.expand_dims(rawdata, axis=0)])

# convert metadata to a DataFrame
md = pd.DataFrame.from_records(recs, columns=recs[0].keys())

# make sure there is one metadata row for each ndarray in the pickle
assert(len(md) == data.shape[0])

# compare checksums
assert(md.loc[0, 'sha1'] == sha1(data[0].ravel()).hexdigest())
assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1].ravel()).hexdigest())

np.save(frames_out, data)
md.to_pickle(metadata_out)