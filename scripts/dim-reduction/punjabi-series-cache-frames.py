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

# for filename in list-of-files:
for path, dirs, files in os.walk(expdir):
    for d in dirs:
        png_glob_exp = os.path.join(path, d, "*.png")
        glob_iter = glob.glob(png_glob_exp)
        if len(glob_iter) > 0: # if there are any .png files in directory
            idx_list = []
            for png in glob_iter:
                # retrieve and sort frame indices from file path strings
                fr_num = re.search('_(\d+).png$', png)
                #print(png, fr_num.group(1))
                idx_list.append(int(fr_num.group(1)))
            start_idx = min(idx_list)
            end_idx = max(idx_list)
            #print(start_idx,end_idx)
            #print(idx_list)
            mid_idx = int(np.floor((start_idx + end_idx)/2))
            try:
                assert mid_idx in idx_list
            except AssertionError:
                print("Desired mid frame index {:} isn't available.".format(mid_idx))
                sys.exit(2)
                
            # get paths for evenly spaced frames between 0th and midpoint frame
            series_frames = []
            for idx in np.linspace(start_idx, mid_idx, num=4):
                idx_int = int(np.floor(idx))
                #rint(idx_int)
                glob_finder = glob.glob(os.path.join(path, d, "*_{:}.png".format(idx_int)))
                if len(glob_finder) == 1:
                    try:
                        # get file path and try to grab some metadata from it
                        frame_path = glob_finder[0]
                        subj, word, block, token, filename = frame_path.split('/')
                    except ValueError:
                        print("Your directories are not structured right. Readjust!")
                        sys.exit(2)
                elif len(glob_finder) > 1:
                    print("Could not find file with desired index {}".format(idx_int))
                    sys.exit(2)
                elif len(glob_finder) < 1:
                    print("Too many files with desired index {}".format(idx_int))
                    sys.exit(2)
                
                # get more metadata from filename
                filename = os.path.splitext(filename)[0]
                filename = re.sub("__", "_", filename)
                subj_dupl, timestamp, idx_dupl = filename.split("_")
                
                # convertingom RGB to grayscale (one-channel):
                print(frame_path)
                inframe = np.asarray(Image.open(frame_path).convert("L")) # converted to uint8:
                rawdata = inframe.astype(np.uint8)
                # TODO filter and ROI somehow (use SRAD) (maybe ROI will have to be skipped?)
                # TODO downsample size of images?
                series_frames.append(rawdata)
            
            #series = np.hstack(series_frames)
            
            if data is None:
                data = np.expand_dims(series_frames, axis=0)
            else:
                data = np.concatenate([data, np.expand_dims(series_frames, axis=0)])
                
            recs.append(
                OrderedDict([
                ('filename', timestamp),
                ('subject', subj),
                ('stim', word),
                ('token', token),
                ('index', idx_int),
                ('sha1', sha1(series_frames[0].ravel()).hexdigest()), # tuple error is thrown here.
                ('sha1_dtype', series_frames[0].dtype)
                ])
            )
            
            # convert metadata to a DataFrame
            md = pd.DataFrame.from_records(recs, columns=recs[0].keys())

            # make sure there is one metadata row for each ndarray in the pickle
            assert(len(md) == data.shape[0])

            # compare checksums
            assert(md.loc[0, 'sha1'] == sha1(data[0][0].ravel()).hexdigest())
            assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1][0].ravel()).hexdigest())

            np.save(frames_out, data)
            md.to_pickle(metadata_out)