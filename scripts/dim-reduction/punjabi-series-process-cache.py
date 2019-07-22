'''
punjabi-series-process-cache.py: process cache as done in Kochetov/Faytak/Nara project.
'''

import argparse
import glob
import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import os
import re
import sys

from hashlib import sha1
from imgphon.imgphon import ultrasound as us
from scipy.ndimage import median_filter

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

yes_no = ["Y", "N"]

subject = "P" + re.sub("[^0-9]", "", expdir)

data_in = os.path.join(expdir,"frames.npy")
data = np.load(data_in)
metadata_in = os.path.join(expdir,'frames_metadata.pickle')
md = pd.read_pickle(metadata_in)

# some sanity checks on data checksums
assert(len(md) == data.shape[0]) # make sure one md row for each frame
assert(md.loc[0, 'sha1'] == sha1(data[0][0].ravel()).hexdigest()) # checksums
assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1][0].ravel()).hexdigest())

# TODO how to get the mean frame object for a 4D array?
# make temp flattened array and take mean of that
data_for_mean = data.reshape([
    data.shape[0] * data.shape[1], 
    data.shape[2],
    data.shape[3]
    ])
#print(data_for_mean.shape)
mean_frame = data_for_mean.mean(axis=0)
#conv_mean = np.flipud(conv.convert(np.flipud(mean_frame)))
plt.title("Mean frame, Spkr {:}".format(subject))
plt.imshow(mean_frame, cmap="Greys_r")
file_ending_mean = "subj{:}_mean.pdf".format(subject)
savepath_mean = os.path.join(expdir,file_ending_mean)
plt.savefig(savepath_mean)
roi_upper = 325
roi_lower = 200
roi_left = 200
roi_right = 400

# TODO give mask converted shape
while True:
    mask = us.roi(mean_frame, 
        upper=roi_upper, 
        lower=roi_lower,
        left=roi_left,
        right=roi_right)
    masked_mean = mean_frame * mask
    #conv_masked = np.flipud(conv.convert(np.flipud(masked_mean)))
    plt.title("Mean frame and RoI, {:}".format(subject))
    plt.imshow(masked_mean, cmap="Greys_r")
    file_ending_roi = "subj{:}_roi.pdf".format(subject)
    savepath_roi = os.path.join(expdir,file_ending_roi)
    plt.savefig(savepath_roi)
    good_roi = input("Inspect {:}. Good RoI? (Y/N) ".format(savepath_roi))

    # TODO improve typo handling
    if good_roi.upper() in yes_no:
        if good_roi.upper() == "Y":
            break
        else:
            roi_upper = int(input("Please provide a new upper bound for RoI (currently {:}): ".format(roi_upper)))
            roi_lower = int(input("Please provide a new lower bound for RoI (currently {:}): ".format(roi_lower)))
            roi_left = int(input("Please provide a new left bound for RoI (currently {:}): ".format(roi_left)))
            roi_right = int(input("Please provide a new right bound for RoI (currently {:}): ".format(roi_right)))
    else:
        print("Typo, try again ...")

adj_radius = int(data[0][0].shape[0]/50) # short side of single frame /50, for median filter

print("Preprocessing data for PCA ...")

in_series = data[0] # array
out_frames_samp = []
padding = 5 # number of pixels to tack on at edges to visually divide frames
for frame in in_series:
    crop_samp = frame[roi_lower:roi_upper, roi_left:roi_right]
    sradd_samp = us.srad(crop_samp)
    clean_samp = us.clean_frame(sradd_samp, median_radius=adj_radius)
#    masked_samp = clean_samp * mask # using mask defined above
    rescaled_samp = clean_samp * 255
    sample_frame = rescaled_samp.astype(np.uint8)
    sample_frame = np.pad(sample_frame, padding, 'constant')
    out_frames_samp.append(sample_frame)

out_series_samp = np.hstack(out_frames_samp)
plt.title("Sample frames series, Spkr {:}".format(subject))
plt.imshow(out_series_samp, cmap="Greys_r")
file_ending_sample = "subj{:}_sample.pdf".format(subject)
savepath_sample = os.path.join(expdir,file_ending_sample)
plt.savefig(savepath_sample)
print("Please check sample series at {}!".format(savepath_sample))

# preallocate ultrasound frame array for PCA
out_serieses = np.empty([data.shape[0]] + list(out_series_samp.shape)) * np.nan
out_serieses = out_serieses.astype('uint8')
filt_hds = []
total = out_serieses.shape[0]

frames_out = "frames_proc.npy"
metadata_out = "frames_proc_metadata.pickle"

# TODO loop index issues (get IndexError "out of range" at item 5)
for idx,series in enumerate(data):
    out_frames = []
    for frame in series:
        crop = frame[roi_lower:roi_upper, roi_left:roi_right]
        sradd = us.srad(crop) 
        clean = us.clean_frame(sradd, median_radius=adj_radius)
        rescaled = clean * 255
        out_frame = rescaled.astype(np.uint8)
        out_frame = np.pad(out_frame, padding, 'constant')
        out_frames.append(out_frame)

    out_series = np.hstack(out_frames)
    out_serieses[idx,:,:] = out_series
    # new sha1 hex: filtered, conv to np.uint8
    filt_hds.append(sha1(out_serieses[idx].ravel()).hexdigest()) 
    print("\tAdded series {} of {}".format(idx+1,total))

# add new sha1 hex as a column in the df
md = md.assign(sha1_filt=pd.Series(filt_hds, index=md.index))

# make sure there is one metadata row for each image frame
assert(len(md) == out_serieses.shape[0])

# for debugging
# pca_md.to_csv(os.path.join(root,d,"test.csv"))

# compare checksums
assert(md.loc[0, 'sha1_filt'] == sha1(out_serieses[0].ravel()).hexdigest())
assert(md.loc[len(md)-1,'sha1_filt'] == sha1(out_serieses[-1].ravel()).hexdigest())
        
 # output
np.save(os.path.join(expdir,frames_out), out_serieses)
md.to_pickle(os.path.join(expdir,metadata_out))