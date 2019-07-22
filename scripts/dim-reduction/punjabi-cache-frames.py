"""
punjabi-cache-frames: frame caching method used in Punjabi dental/retroflex project (Kochetov, Faytak, Nara)
"""

# TODO: actually using?
from __future__ import absolute_import, division, print_function

import argparse
import glob
import numpy as np
import os
import pandas as pd
import re
import struct
import subprocess
import sys

from collections import OrderedDict
from hashlib import sha1
from operator import itemgetter
from PIL import Image
from scipy import ndimage

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
png_glob_exp = os.path.join(os.path.normpath(expdir),"*.png")

# for filename in list-of-files:
for filename in glob.glob(png_glob_exp): 

    # get filename and other metadata
    fname = os.path.split(filename)[1]
    fname_bare = os.path.splitext(fname)[0]
    attr = fname_bare.split('_')
    subj = attr[0]
    lang = re.sub(r'[0-9]', '', attr[0]) 

    # subj is crucial for subsetting data. Users will want to define this on their own.
    # But it might be good to have a function with flat directory structure and subj IDs as inputs...
    # ...that caches all data at once.
    # this would let people select their desired frame subset however they'd like, and then run all at once.
    # on the other hand, having subject as a variable and pulling the data apart is much easier conceptually, and the data is easier to move around as a single large file.

    if len(attr) > 2:
        stim = attr[1] 
        token = re.sub(r'[a-zA-Z]', '', attr[2]) 

    else:
        stim = re.sub(r'[0-9]', '', attr[1])  
        token = re.sub(r'[a-zA-Z]', '', attr[1]) 

    if stim in ["banab", "batab"]:
        place = "alv"
        if stim == "banab":
            phone = "n"
        else:
            phone = "t"
    elif stim in ["baNab", "baTab"]:
        place = "ret"
        if stim == "baNab":
            phone = "nr"
        else:
            phone = "tr"

    # get ndarray from image file. issue is probably here. Unconverted RGB:
    inframe = np.asarray(Image.open(filename)) 
    # converted from RGB to grayscale (one-channel):
    inframe = np.asarray(Image.open(filename).convert("L")) 
    # converted to uint8:
    rawdata = inframe.astype(np.uint8)
    # the ravel() seems to work correctly, at least in terms of producing an array of the right size:

    # generate metadata object for the current acquisition

    recs.append(
            OrderedDict([
                ('filename', fname), 
                ('subject', subj),
                ('stim', stim),
                ('token', token),
                ('phone', phone), 
                ('place', place),
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
