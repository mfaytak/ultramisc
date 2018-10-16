import os, sys, glob, re
import argparse
import numpy as np 
import pandas as pd
# from ultratils.pysonix.scanconvert import Converter # not needed for Toronto data
from hashlib import sha1
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from scipy.ndimage import median_filter
import matplotlib.pyplot as plt
# % matplotlib inline

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

data_in = os.path.join(expdir,"frames.npy")
data = np.load(data_in)
metadata_in = os.path.join(expdir,"frames_metadata.pickle")
md = pd.read_pickle(metadata_in)

# sanity checks
assert(len(md) == data.shape[0]) # make sure one md row for each frame
assert(md.loc[0, 'sha1'] == sha1(data[0].ravel()).hexdigest()) # checksums
assert(md.loc[len(md)-1,'sha1'] == sha1(data[-1].ravel()).hexdigest())

n_pca = 4
#n_lda = 1
image_shape = data[0].shape # base off of first frame

subject = []
phase = []
trial = []
phone = []

for s in np.unique(md['subject']):
	# subset data by subject ID
	subj_mask = (md['subject'] == s) 
	subj_mask = subj_mask.as_matrix()
	model_data = data[subj_mask]
	model_md = md[subj_mask]
			
	# preallocate array for ultrasound frames for PCA
	model_array = np.empty([model_data.shape[0]] + list(model_data[0].shape)) * np.nan
	model_array = model_array.astype('uint8')
		
	# fill in the preallocated array, applying median filter (and any other desired transforms)
	for idx,frame in enumerate(model_data):
		filt_frame = median_filter(frame, 5)
		model_array[idx,:,:] = filt_frame # frame
	
	# run PCA with three PCs
	n_components = int(n_pca)
	pca = PCA(n_components=int(n_components)) 
	array_reshaped = model_array.reshape([
				model_array.shape[0],
				model_array.shape[1] * model_array.shape[2]
				])
	pca.fit(array_reshaped)
	cumulative_var_exp = sum(pca.explained_variance_ratio_)

	print("Subj.{}: PCA with {} PCs explains {} of variation".format(s,
			n_components,
			round(cumulative_var_exp,4)
			))

	pca_out = pca.transform(array_reshaped)

	# output PC values by acquisition

	# create output table headers
	pc_headers = ["pc"+str(i+1) for i in range(0,n_components)] # n. of PC columns changes acc. to n_components
	meta_headers = list(md.columns.values)
	headers = meta_headers + pc_headers

	# create output table
	headless = np.column_stack((md[meta_headers], pca_out))
	d = np.row_stack((headers, headless)) 

	out_filename = "{}_pca.csv".format(s)
	out_path = os.path.join(expdir,out_filename)
	np.savetxt(out_path, d, fmt="%s", delimiter ='\t')

	# TODO once relevant, output one table across multiple subjects?

	# output eigentongues
	if n_components < 5:
		n_output_pcs = n_components
	else:
		n_output_pcs = 5

	for n in range(0,n_output_pcs):
		dd = pca.components_[n].reshape(image_shape)
		mag = np.max(dd) - np.min(dd)
		pc_load = (dd-np.min(dd))/mag*255
		plt.title("PC{:} min/max loadings, Subj. {:}".format((n+1),s))
		plt.imshow(pc_load, cmap="Greys_r")
		file_ending = "{:}-pc{:}.pdf".format(s, (n+1))
		savepath = os.path.join(expdir,file_ending) # TODO redefine save path if needed
		plt.savefig(savepath)