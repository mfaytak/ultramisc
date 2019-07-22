'''
punjabi-series-pca-lda: PCA-LDA pipeline as used for Punjabi time series project (Kochetov, Faytak, Nara)
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
from scipy.ndimage import median_filter
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA

# read in args
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
parser.add_argument("--pca_dim", "-p", help="Number of principal components to retain")
parser.add_argument("--lda_dim", "-l", help="Number of linear discriminants to use")
parser.add_argument("training", help="Set of observations to train LDA on")
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

subj = "P" + re.sub("[^0-9]","",expdir)

data_in = os.path.join(expdir,"frames_proc.npy")
data = np.load(data_in)
metadata_in = os.path.join(expdir,"frames_proc_metadata.pickle")
md = pd.read_pickle(metadata_in)

# sanity checks
assert(len(md) == data.shape[0]) # make sure one md row for each frame
assert(md.loc[0, 'sha1_filt'] == sha1(data[0].ravel()).hexdigest()) # checksums
assert(md.loc[len(md)-1,'sha1_filt'] == sha1(data[-1].ravel()).hexdigest())

# TODO subset by words of interest
model_array = data
model_md = md 

image_shape = model_array[0].shape

print("Now running PCA...")

n_components = int(args.pca_dim)
pca = PCA(n_components=int(n_components)) 

array_reshaped = model_array.reshape([
				model_array.shape[0],
				model_array.shape[1] * model_array.shape[2]
				])
pca.fit(array_reshaped)
cumulative_var_exp = sum(pca.explained_variance_ratio_)

print("{}:\tPCA with {} PCs explains {} of variation".format(subj,
		n_components,
		round(cumulative_var_exp,4)
		))

pca_out = pca.transform(array_reshaped)

# create output table headers
pc_headers = ["pc"+str(i+1) for i in range(0,n_components)] # n. of PC columns changes acc. to n_components
meta_headers = list(md.columns.values)
headers = meta_headers + pc_headers

# create output table
headless = np.column_stack((md[meta_headers], pca_out))
d = np.row_stack((headers, headless)) 

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
	plt.title("PC{:} min/max loadings, {:}".format((n+1),subj))
	#plt.title("PC{:} min/max loadings, ".format((n+1)))
	plt.imshow(pc_load, cmap="Greys_r")
	file_ending = "{:}-pc{:}.pdf".format(subj, (n+1))
	#file_ending = "all-pc{:}.pdf".format((n+1))
	savepath = os.path.join(expdir,file_ending) # TODO redefine save path if needed
	plt.savefig(savepath)

pca_out = pca.transform(array_reshaped)

# now LDA stuff

# select training and testing sets based on input
if args.training == "stops":
	print("Now running LDA (trained on stops)...")
	training_list = ["batab", "batrab"]
	test_list = ["banab", "banrab"]
elif args.training == "nasals":
	print("Now running LDA (trained on nasals)...")
	training_list = ["banab", "banrab"]
	test_list = ["batab", "batrab"]
else:
	print("Could not interpret requested training set, exiting")
	sys.exit(2)

training_mask = model_md['stim'].isin(training_list)
training_mask = training_mask.values
training_md = model_md[training_mask].copy()
training_data = pca_out[training_mask]

test_mask = model_md['stim'].isin(test_list)
test_mask = test_mask.values
test_md = model_md[test_mask].copy()
test_data = pca_out[test_mask]

# train LDA on training data
labs = [re.sub("[biau]","", s) for s in np.array(training_md.stim)] # expand dims?
test_labs = [re.sub("[biau]","", s) for s in np.array(test_md.stim)]
cats = ["retroflex" if s in ["tr","nr"] else "dental" for s in labs]
test_cats = ["retroflex" if s in ["tr","nr"] else "dental" for s in test_labs]

train_lda = LDA(n_components = int(args.lda_dim))
train_lda.fit(training_data, cats) # train the model on the data
train_lda_out = train_lda.transform(training_data) 

# validate by scoring on training data
train_score = train_lda.score(training_data, cats)
print("{}:\tLDA (1 LD) correctly classifies {} of training {}".format(subj, train_score, args.training))

# score and/or categorize test data according to trained LDA model
if args.training == "stops":
	test_class = "nasals"
else:
	test_class = "stops"

test_lda_out = train_lda.transform(test_data) 

# show score for test data
test_score = train_lda.score(test_data, test_cats)
print("{}:\tLDA (1 LD) correctly classifies {} of test {}".format(subj, test_score, test_class))

# PCA and LDA outputs
# LDA data for csv: training on top of test
ld = pd.DataFrame(np.vstack([train_lda_out, test_lda_out]))
ld = ld.rename(columns = {0:'LD1', 1:'LD2'})

# make PCs into a set of columns
pc_dataframe = pd.DataFrame(pca_out)
pc_dataframe = pc_dataframe.rename(columns=lambda x: "pc"+str(int(x)+1))

# metadata that was read in earlier for csv: training on top of test
out_md = pd.concat([training_md, test_md], axis=0, ignore_index=True)

# classification results: training on top of test
cls = pd.concat(
        [pd.DataFrame(train_lda.predict(training_data)), 
         pd.DataFrame(train_lda.predict(test_data))],
        axis=0,
        ignore_index=True
         )
cls = cls.rename(columns = {0:'cls'})

# combine all of the above into a DataFrame object
ld_md = pd.concat([out_md, ld, cls, pc_dataframe], axis=1)

# save analysis data for the current subject as csv
csv_path = os.path.join(expdir, "{:}_ldas_train_{:}.csv".format(subj, args.training))

ld_md.to_csv(csv_path, index=False)

# TODO validate by classifying on training data
# TODO classification pcts.?