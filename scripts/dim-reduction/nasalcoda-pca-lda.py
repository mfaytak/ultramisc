'''
nasalcoda-pca-lda: PCA-LDA pipeline as used in nasal coda project (Liu S., Faytak).
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
from imgphon.ultrasound import reconstruct_frame
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
parser.add_argument("--pca_dim", "-p", help="Number of principal components to retain")
parser.add_argument("--lda_dim", "-l", help="Number of linear discriminants to train")
parser.add_argument("--flop", "-f", help="Horizontally flip the data", action="store_true")
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

for root, dirs, files in os.walk(expdir):
	for d in dirs:
		if d.startswith("."): # don't run on MAC OS hidden directories
			continue
		subject = re.sub("[^0-9]","",d) # subject is any numbers in directory name
		data_in = os.path.join(root,d,"frames_proc.npy")
		data = np.load(data_in)
		metadata_in = os.path.join(root,d,'frames_proc_metadata.pickle')
		md_pre = pd.read_pickle(metadata_in)
		# check that metadata matches data, frame-by-frame
		assert(len(md_pre) == data.shape[0])
		for idx,row in md_pre.iterrows():
			assert(row['sha1_filt'] == sha1(data[idx].ravel()).hexdigest())
		# get rid of hash columns after checking
		md = md_pre.iloc[:,0:11].copy() 
		
		# break off nasals specifically (vowels are in these data sets, too)
		nas_mask = md['phone'].isin(['n','ng'])
		pca_data = data[nas_mask]
		pca_md = md[nas_mask]

		if args.flop:
			 # flips all frames on their second axis, i.e. front-back
			pca_data = np.flip(pca_data, 2)

		# reshape data to prep for PCA
		image_shape = pca_data[0].shape
		frames_reshaped = pca_data.reshape([
				pca_data.shape[0],
				pca_data.shape[1] * pca_data.shape[2]
				])
		
		# carry out PCA
		pca = PCA(n_components=n_components) 
		pca.fit(frames_reshaped)
		total_var_exp = sum(pca.explained_variance_ratio_)
		pcvar = pca.explained_variance_ratio_

		pca_out = pca.transform(frames_reshaped)
		
		pc_filestring = "NC{:}_pcs.csv".format(subject)
		pc_savepath = os.path.join(root,d,pc_filestring) 
		pc_headers = ["pc"+str(i+1) for i in range(0,n_components)]
		meta_headers = pca_md.columns.values
		headers = list(meta_headers) + pc_headers
		metadata = pca_md.values # md.as_matrix(columns = md.columns[0:11])
		out_df = np.row_stack((headers,
					np.column_stack((metadata, pca_out))
					))
		np.savetxt(pc_savepath, out_df, fmt="%s", delimiter = ',')

		print("Subj.{}: PCA with {} PCs explains {} of variation".format(subject, str(n_components),
																round(total_var_exp,4)
																))
		print(pca.explained_variance_ratio_)
		
		# output 
		for n in range(0,n_components):
			dd = pca.components_[n].reshape(image_shape)
			mag = np.max(dd) - np.min(dd)
			pc_load = (dd-np.min(dd))/mag*255
			plt.title("PC{:} eigentongue, Subj {:}".format((n+1),subject))
			plt.imshow(pc_load, cmap="Greys_r")
			file_ending = "subj{:}-pc{:}-filt.pdf".format(subject, (n+1))
			savepath = os.path.join(root,d,file_ending)
			plt.savefig(savepath)
			
		vectors = pca.components_
		pca_md.reset_index(drop=True, inplace=True) # in case there was any subsetting

		in_mask = (pca_md['phone'].isin(['n']) & pca_md['before'].isin(['i']))
		ing_mask = (pca_md['phone'].isin(['ng']) & pca_md['before'].isin(['i']))
		en_mask = (pca_md['phone'].isin(['n']) & pca_md['before'].isin(['e']))
		eng_mask = (pca_md['phone'].isin(['ng']) & pca_md['before'].isin(['e']))
		an_mask = (pca_md['phone'].isin(['n']) & pca_md['before'].isin(['a']))
		ang_mask = (pca_md['phone'].isin(['ng']) & pca_md['before'].isin(['a']))
		uan_mask = (pca_md['phone'].isin(['n']) & pca_md['before'].isin(['ua']))
		uang_mask = (pca_md['phone'].isin(['ng']) & pca_md['before'].isin(['ua']))

		# make dict of masks and strings for plot labels/output titles
		output_dict = {"in": in_mask,
					  "ing": ing_mask,
					  "en": en_mask,
					  "eng": eng_mask,
					   "an": an_mask,
					  "ang": ang_mask,
					  "uan": uan_mask,
					  "uang": uang_mask}

		SMALL_SIZE = 8
		MEDIUM_SIZE = 10
		BIGGER_SIZE = 12

		for label in output_dict:
			idx_list = pca_md.index[output_dict[label]].tolist() # subset pca_md by each mask
			values = pca_out[idx_list]

			plt.rcParams['font.sans-serif'] = "Noto Sans UI"
			#plt.rcParams['font.family'] = "sans-serif"

			SMALL_SIZE = 8
			MEDIUM_SIZE = 10
			#BIGGER_SIZE = 14

			plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
			plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
			plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
			plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
			plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize

			plt.title("Reconstructed {:}, speaker {:}".format(label.upper(), subject))
			# TODO need to get max/min values out of reconstruct_frame somehow
			plt.imshow(reconstruct_frame(vectors, values, pca.n_components, image_shape), cmap="Blues_r")
			clb = plt.colorbar(extend='min', shrink=0.55)
			clb.ax.set_title('Pixel\n value')
			plt.clim(0)
			file_ending = "subj{:}-{:}-recon.pdf".format(subject, label)
			savepath = os.path.join(root,d,file_ending)
			plt.savefig(savepath)
			plt.close("all")
		
		# now LDA
		training_list = ["n", "ng"]
		training_mask = pca_md['phone'].isin(training_list)
		training_mask = training_mask.values
		training_md = pca_md[training_mask].copy()
		training_data = pca_out[training_mask]
		
		# train LDA on training data
		labs = np.array(training_md.phone) # expand dims?
		train_lda = LDA(n_components = int(n_lds))
		train_lda.fit(training_data, labs) # train the model on the data
		train_lda_out = train_lda.transform(training_data) 
		
		# save LDs for visualization
		ld = pd.DataFrame(np.vstack([train_lda_out]))
		ld = ld.rename(columns = {0:'LD1'})
		subject_lab = [subject] * ld.shape[0]
		subject_column = pd.DataFrame(subject_lab)
		subject_column = subject_column.rename(columns = {0:'subj'})
		md = training_md
		
		# get classification results
		cls = pd.DataFrame(train_lda.predict(training_data))
		cls = cls.rename(columns = {0:'cls'})
		
		# combine all of the above into a DataFrame object and save
		for df in [subject_column, ld, cls, training_md]:
			df.reset_index(drop=True, inplace=True)
		ld_md = pd.concat([subject_column, ld, cls, training_md], axis=1)
		lda_savepath = os.path.join(root,d,"NC{:}_ldas_1ld.csv".format(subject))
		ld_md.to_csv(lda_savepath, index=False)

		# TODO output total token counts and token counts for each bin
		print("FRAME COUNT")
		print("\t" + "Total nasal frames analyzed: {:} ".format(pca_data.shape[0]))
		for label in output_dict:
			count = sum(output_dict[label]) # add up TRUEs in the masks
			print("\t" + "Total frames for {:}, subj {:}: {:}".format(label.upper(), subject, count))

		
		# print pct correct classification of training data
		print("LDA ACCURACY")
		print("\t" + subject + ": overall correct = " + str(train_lda.score(training_data, labs)))

		before_labels = list(np.unique(ld_md.before)) # [a, e, i, ua]
		train_labels = list(np.unique(ld_md.phone))

		for b in before_labels: # [a, e, i, ua]
			set_by_before = ld_md.loc[ld_md.before == b]
			for tr in train_labels: # [n, ng]
				set_by_before_coda = set_by_before.loc[set_by_before.phone == tr]
				total_count = set_by_before_coda.shape[0]
				correct_subset = set_by_before_coda.loc[set_by_before_coda.cls == tr]
				correct_count = correct_subset.shape[0]
				prop_correct = correct_count/total_count
				print('\t', b+tr, '\t proportion correct (as {})'.format(tr), prop_correct)
