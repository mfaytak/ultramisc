'''
suzhou-pca-lda-1ld: PCA-LDA method, Suzhou project, simple (1LD) model.
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
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA

def coart_class(row):
	# figure out how to make training words just be "training"
	if row['pron'] in test_no_coart_words:
		return "no_fric"
	elif row['pron'] in apical_words:
		return "apical"
	else:
		return "fric"

# label test case by word type in metadata - coart from fric or not (or apical, or test)
test_no_coart_words = ["IZ", "BIZX", "YZ"] # mark as "no_coart" 
apical_words = ["SZ", "SZW"] # third level "apical"; useless for comparisons

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
parser.add_argument("--pca_dim", "-p", help="Number of principal components to retain")
parser.add_argument("--lda_dim", "-l", help="Number of linear discriminants to use")
#parser.add_argument("-v", "--visualize", help="Produce plots of PC loadings on fan",action="store_true")
args = parser.parse_args()

try:
	expdir = args.directory
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

n_components = int(args.pca_dim)
n_lds = int(args.lda_dim)

pct_out = "percent_classified_1ld.txt" 
pct_out_path = os.path.join(expdir,pct_out)
pct_out_head = "\t".join(["subj", "test", "coart", "classified_as", "pct_class"]) 
with open(pct_out_path, "w") as out:
	out.write(pct_out_head + "\n")

for root,directories,files in os.walk(expdir):
	for d in directories:

		if d.startswith("."):
			continue

		subject = re.sub("[^0-9]","",d)

		data_in = os.path.join(root,d,"frames_proc.npy")
		data = np.load(data_in)
		metadata_in = os.path.join(root,d,'frames_proc_metadata.pickle')
		md_pre = pd.read_pickle(metadata_in)

		# some sanity checks on data checksums
		assert(len(md_pre) == data.shape[0]) # make sure one md row for each frame
		assert(md_pre.loc[0, 'sha1_filt'] == sha1(data[0].ravel()).hexdigest()) # checksums
		assert(md_pre.loc[len(md_pre)-1,'sha1_filt'] == sha1(data[-1].ravel()).hexdigest())
		# get rid of hash-related columns after checking
		md = md_pre.iloc[:,0:11].copy() 

		# subset data again to remove unneeded data
		vow_mask = (md['pron'].isin(["BIY", "IY", "XIY", "SIY", "BIZX", "IZ", "SIZ", "XIZ", "YZ", "XYZ"])) & (md['phone'] != "SH") & (md['phone'] != "S")
		sh_mask = (md['pron'].isin(["XIZ", "XYZ", "XIY", "XIEX", "XEU"])) & (md['phone'] == "SH")
		#s_mask = (md['pron'].isin(["SAAE", "SEI", "SUW", "SIEX", "SOOW", "SZ", "SZW"])) & (md['phone'] == "S")       
		mask = vow_mask | sh_mask
		mask = mask.values
		pca_data = data[mask]
		pca_md = md[mask]

		image_shape = pca_data[0].shape

		# reshape 2D frame data into 1D vectors and fit PCA
		frames_reshaped = pca_data.reshape([
				pca_data.shape[0],
				pca_data.shape[1] * pca_data.shape[2]
				])
		pca = PCA(n_components=n_components) 
		pca.fit(frames_reshaped)
		total_var_exp = sum(pca.explained_variance_ratio_)
		pcvar = pca.explained_variance_ratio_

		# output PC loading plots, with different names from full LDA
		if n_components < 6:
			n_output_pcs = n_components
		else:
			n_output_pcs = 6

		# save scree plots
		plt.title("Scree plot, subj. {:}".format(subject))
		plt.plot(np.cumsum(pcvar) * 100)
		scree_ending = "subj{:}-scree-1ld.pdf".format(subject)
		screepath = os.path.join(root,d,scree_ending)
		plt.savefig(screepath)

		for n in range(0,n_output_pcs):
			dd = pca.components_[n].reshape(image_shape)
			mag = np.max(dd) - np.min(dd)
			pc_load = (dd-np.min(dd))/mag*255
			# conversion would happen here if images weren't converted already
			plt.title("PC{:} min/max loadings, subj {:}".format((n+1),subject))
			plt.imshow(pc_load, cmap="Greys_r")
			file_ending = "subj{:}-pc{:}-filt-1ld.pdf".format(subject, (n+1))
			savepath = os.path.join(root,d,file_ending)
			plt.savefig(savepath)

		# print some info
		print("\tSubj.{}: PCA with {} PCs explains {} of variation".format(subject, str(n_components),
															round(total_var_exp,4)
															))

		pca_out = pca.transform(frames_reshaped)

		# output PC scores
		pc_filestring = "suzh{:}_pcs_1ld.csv".format(subject)
		pc_savepath = os.path.join(root,d,pc_filestring) 
		pc_headers = ["pc"+str(i+1) for i in range(0,n_components)]
		meta_headers = md.columns.values
		headers = list(meta_headers) + pc_headers
		metadata = pca_md.values # md.as_matrix(columns = md.columns[0:11])
		out_df = np.row_stack((headers,
						 np.column_stack((metadata, pca_out))
						 ))
		np.savetxt(pc_savepath, out_df, fmt="%s", delimiter = ',')

		# subset PCA'ed data into training and testing sets
		training_list = ["IY1", "SH"] 

		# encode as a factor whether there's a fricative or not
		# TODO: check this (why SIZ?)
		test_list = ["IZ1", "YZ1"] 
		test_coart_words = ["XIZ", "SIZ", "XYZ"] # mark as "coart"
		test_no_coart_words = ["IZ", "BIZX", "YZ"] # mark as "no_coart" 
		# apical_words = ["SZ", "SZW"] # third level "apical"; useless for comparisons

		training_mask = pca_md['phone'].isin(training_list)
		training_mask = training_mask.values
		training_md = pca_md[training_mask].copy()
		training_data = pca_out[training_mask]

		test_mask = pca_md['phone'].isin(test_list)
		test_mask = test_mask.values
		test_md = pca_md[test_mask].copy()
		test_data = pca_out[test_mask]

		# train LDA on training data
		labs = np.array(training_md.phone) # expand dims?
		train_lda = LDA(n_components = int(n_lds))
		train_lda.fit(training_data, labs) # train the model on the data
		train_lda_out = train_lda.transform(training_data) 

		# score and/or categorize test data according to trained LDA model
		test_lda_out = train_lda.transform(test_data) 

		# LDA data for csv: training on top of test
		ld = pd.DataFrame(np.vstack([train_lda_out, test_lda_out]))
		ld = ld.rename(columns = {0:'LD1', 1:'LD2'})

		# a subject column for csv
		subject_lab = [subject] * ld.shape[0]
		subject_column = pd.DataFrame(subject_lab)
		subject_column = subject_column.rename(columns = {0:'subj'})

		training_md["coart_class"] = ["training"] * training_md.shape[0]
		test_md["coart_class"] = test_md.apply(lambda row: coart_class (row),axis=1)

		# metadata that was read in earlier for csv: training on top of test
		md = pd.concat([training_md, test_md], axis=0, ignore_index=True)

		# classification results: training on top of test
		cls = pd.concat(
			[pd.DataFrame(train_lda.predict(training_data)), 
			 pd.DataFrame(train_lda.predict(test_data))],
			axis=0,
			ignore_index=True
			)
		cls = cls.rename(columns = {0:'cls'})

		# combine all of the above into a DataFrame object
		ld_md = pd.concat([subject_column, ld, cls, md], axis=1)

		# TODO the below is not quite how you were calculating the score
		# add range-normalized linear discriminant values to DataFrame
		# ld_range = max(ld_md.LD) - min(ld_md.LD)
		# ld_md = ld_md.assign(normLD = (ld_md.LD - min(ld_md.LD)) / ld_range )

		# save analysis data for the current subject as csv
		lda_savepath = os.path.join(root,"suzh_{:}_ldas_1ld.csv".format(subject))
		ld_md.to_csv(lda_savepath, index=False)

		# output classification results
		laminal_list = ["IZ1", "YZ1"]
		apical_list = ["ZZ1", "ZW1"]
		train_labels = list(np.unique(training_md.phone))
		test_labels = list(np.unique(test_md.phone))
		coart_types = list(np.unique(ld_md.coart_class))

		# fricative vowel classification by training category and coarticulatory class
		rows_laminal = ld_md.loc[(ld_md.phone == "IZ1") | (ld_md.phone == "YZ1")]
		for c in coart_types:
			if c not in ["fric", "no_fric"]:
				continue 
			rows_by_co = rows_laminal.loc[rows_laminal.coart_class == c]
			for t in train_labels:
				rows_by_clco = rows_by_co.loc[rows_by_co.cls == t]
				prop_class = round(rows_by_clco.shape[0]/rows_by_co.shape[0], 4)
				print("\t{}, coart {} \t classified as {} -- {}".format("laminal",c,t,prop_class))
				with open(pct_out_path, "a") as out:
					out.write("\t".join([subject,"laminal",c,t,str(prop_class)]) + "\n")
			print("\t---")

 # gather and open all csv files in directory, then put together into one csv file
big_ld_list = []
for root,directories,files in os.walk(expdir):
	for f in files:
		if f.endswith("ldas_1ld.csv"):
			csv_back_in = os.path.join(root,f)
			one_subj = pd.read_csv(csv_back_in)
			big_ld_list.append(one_subj)

big_ld = pd.concat(big_ld_list, axis=0)
big_ld_csv_path = os.path.join(expdir,"suzhou_all_subj_ldas_1ld.csv")
big_ld.to_csv(big_ld_csv_path, index=False)

# do the same for PCs
big_pc_list = []
for root,directories,files in os.walk(expdir):
	for f in files:
		if f.endswith("pcs_1ld.csv"):
			csv_back_in = os.path.join(root,f)
			one_subj = pd.read_csv(csv_back_in)
			big_pc_list.append(one_subj)

big_pc = pd.concat(big_pc_list, axis=0)
big_pc_csv_path = os.path.join(expdir,"suzhou_all_subj_pcs_1ld.csv")
big_pc.to_csv(big_pc_csv_path, index=False)