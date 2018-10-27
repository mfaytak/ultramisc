import os, sys, glob, re
import argparse
import numpy as np 
import pandas as pd
from ultratils.pysonix.scanconvert import Converter
from hashlib import sha1
from sklearn.decomposition import PCA
from scipy.ndimage import median_filter
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
import matplotlib.pyplot as plt
from imgphon.imgphon import ultrasound as us
import concurrent.futures

yes_no = ["Y", "N"]

def read_echob_metadata(rawfile):
	'''
	Gather information about a .raw file from its .img.txt file. 
	For legacy .raw data without a header; if a header exists,
	use ultratils utilities.
	Inputs: a .raw file, which is assumed to have an .img.txt file
	  with the same base name.
	Outputs:
	  nscanlines, the number of scan lines ("width" of unconverted img)
	  npoints, the number of pixels in each scan line ("height" of img)
	  not_junk, the pixel index in each scan line where junk data begins
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


def conversion_helper(frame, mask):
	roi_frame = frame * mask
	conv_roi_frame = np.flipud(conv.convert(np.flipud(roi_frame)))
	srad_frame = us.srad(conv_roi_frame)
	clean_frame = us.clean_frame(srad_frame)
	return clean_frame

# TODO make sure this is assigning a label to everything
def coart_class(row):
	# figure out how to make training words just be "training"
	if row['pron'] in test_no_coart_words:
		return "no_fric"
	elif row['pron'] in apical_words:
		return "apical"
	else:
		return "fric"

# instantiate converter for pca_data images
class Header(object):
	def __init__(self):
		pass

class Probe(object):
	def __init__(self):
		pass
# to be defined below on first pass through data
conv = None

# sample frame output
sample_frame = None

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
#parser.add_argument("n_pca", help="Number of principal components to start with")
#parser.add_argument("n_lda", help="Number of linear discriminant functions to output")
#parser.add_argument("-v", "--visualize", help="Produce plots of PC loadings on fan",action="store_true")
args = parser.parse_args()

try:
	expdir = args.directory
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

#header = '\t'.join(['subject','phone','LD'])
#with open('suzhou_norm_medians.txt','w') as out:
#    out.write(header + '\n')

#pct_out = "percent_classified.txt" 
#pct_out_head = "\t".join(["subj", "test", "coart", "classified_as", "pct_class"]) 
#with open(pct_out, "w") as out:
#	out.write(pct_out_head + "\n")

frames_out = "frames_proc.npy"
metadata_out = "frames_proc_metadata.pickle"

# label test case by word type in metadata - coart from fric or not (or apical, or test)
test_no_coart_words = ["IZ", "BIZX", "YZ"] # mark as "no_coart" 
apical_words = ["SZ", "SZW"] # third level "apical"; useless for comparisons

for root,directories,files in os.walk(expdir):

	# TODO RoI stuff diff. for each subj

	for d in directories:

		subject = re.sub("[^0-9]","",d)

		data_in = os.path.join(root,d,"frames.npy")
		data = np.load(data_in)
		metadata_in = os.path.join(root,d,'frames_metadata.pickle')
		md = pd.read_pickle(metadata_in)

		# some sanity checks on data checksums
		assert(len(md) == data.shape[0]) # make sure one md row for each frame
		assert(md.loc[0, 'sha1'] == sha1(data[0].ravel()).hexdigest()) # checksums
		assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1].ravel()).hexdigest())

		# subset data
		#training_list = ["IY1", "SH"] # for use later
		#test_list = ["IZ1"] # for use later
		vow_mask = (md['pron'].isin(["BIY", "IY", "XIY", "SIY", "BIZX", "IZ", "SIZ", "XIZ", "YZ", "XYZ", "SZ", "SZW"])) & (md['phone'] != "SH") & (md['phone'] != "S")
		sh_mask = (md['pron'].isin(["XIZ", "XYZ", "XIY", "XIEX", "XEU"])) & (md['phone'] == "SH")
		s_mask = (md['pron'].isin(["SAAE", "SEI", "SUW", "SIEX", "SOOW", "SZ", "SZW"])) & (md['phone'] == "S")
		mask = vow_mask | sh_mask | s_mask
		mask = mask.as_matrix()
		pca_data = data[mask]
		pca_md = md[mask]

		# define Converter parameters from first acq for first subj
		# this will break if data from more than one ultrasound system is processed simultaneously
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
		roi_upper = 600
		roi_lower = 300

		while True:
			mask = us.roi(mean_frame, upper=roi_upper, lower=roi_lower)
			masked_frame = mean_frame * mask
			conv_masked = np.flipud(conv.convert(np.flipud(masked_frame)))
			plt.title("Mean frame and RoI, Spkr {:}".format(subject))
			plt.imshow(conv_masked, cmap="Greys_r")
			file_ending_roi = "subj{:}_roi.pdf".format(subject)
			savepath_roi = os.path.join(root,d,file_ending_roi)
			plt.savefig(savepath_roi)
			good_roi = input("Inspect {:}. Good RoI? (Y/N) ".format(savepath_roi))

			# TODO improve typo handling
			if good_roi in yes_no:
				if good_roi == "Y":
					break
				else:
					roi_upper = int(input("Please provide a new upper bound for RoI (currently) {:}: ".format(roi_upper)))
					roi_lower = int(input("Please provide a new lower bound for RoI (currently) {:}: ".format(roi_lower)))
			else:
				print("Typo, try again ...")

		# preallocate ultrasound frame array for PCA
		conv_frame = conv.convert(pca_data[0])
		pca_frames = np.empty([pca_data.shape[0]] + list(conv_frame.shape)) * np.nan
		pca_frames = pca_frames.astype('uint8')

		print("Preprocessing data for PCA ...")

		total = pca_frames.shape[0]

		# fill in preallocated array
		# TODO parallelize this part
		# TODO or perhaps the SRAD function

		filt_hds = []

		if sample_frame is None:
			in_sample = pca_data[0]
			roi_frame = in_sample * mask
			conv_roi_frame = np.flipud(conv.convert(np.flipud(roi_frame)))
			srad_frame = us.srad(conv_roi_frame)
			clean_frame = us.clean_frame(srad_frame)
			plt.title("Sample frame, Spkr {:}".format(subject))
			plt.imshow(clean_frame, cmap="Greys_r")
			file_ending_sample = "subj{:}_sample.pdf".format(subject)
			savepath_sample = os.path.join(root,d,file_ending_sample)
			plt.savefig(savepath_sample)
			print("Please check sample frame at {}!".format(savepath_sample))

		for idx,frame in enumerate(pca_data):
			# see helper function
			roi_frame = frame * mask
			conv_roi_frame = np.flipud(conv.convert(np.flipud(roi_frame)))
			srad_frame = us.srad(conv_roi_frame)
			clean_frame = us.clean_frame(srad_frame)

			pca_frames[idx,:,:] = clean_frame
			filt_hds.append(sha1(clean_frame.ravel()).hexdigest()) # new sha1 hex
			print("\tAdded frame {} of {}".format(idx+1,total))

		# TODO add new sha1 hex as a column in the df

		filt_hds_col = pd.Series(filt_hds)
		pca_md["sha1_filt"] = filt_hds_col.values

		# make sure there is one metadata row for each image frame
		assert(len(pca_md) == pca_frames.shape[0])

		# compare checksums
		assert(pca_md.loc[0, 'sha1_filt'] == sha1(pca_frames[0].ravel()).hexdigest())
		assert(pca_md.loc[len(md)-1,'sha1_filt'] == sha1(pca_frames[-1].ravel()).hexdigest())

		np.save(os.path.join(root,d,frames_out), pca_frames)
		pca_md.to_pickle(os.path.join(root,d,metadata_out))