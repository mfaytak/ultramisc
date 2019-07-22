#### 2019 TAP/FlAP ULTRASOUND PROJECT ####
## Script for moving acquisitions into folders sorted by the type of tap/flap
## inter-rater disagreement. 
## Jennifer Kuo July 2019

## TO run: python move-for-recoding.py EXPDIR CODEFILE
## Where: EXPDIR is the directory containing the experiment files (acquisitions), 
## and CODEFILE is the csv file with all the coding results.

import argparse
import os
import pandas as pd
import shutil

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("expdir",
					help="Experiment directory containing all subjects'\
						  caches and metadata in separate folders"
					)
parser.add_argument("codefile", action="store",
					help="Name of csv file with coding results"
					)

args = parser.parse_args()

expdir = args.expdir
codefile = args.codefile

## read coding csv file
coding_results = pd.read_csv(codefile,sep=',')

## loop through rows of the coding file 
#(each row corresponding to one acquisition)
for i,j in coding_results.iterrows():
	## 
	acq = j[0] #name of acquisition (timestamp)
	err_type = j[14] #type of inter-rater mismatch
	start_dir = os.path.join(expdir,acq) 
	out_dir = os.path.join(expdir + '_recode',err_type) 

	# if acquisition exists in expdir, move it to a subfolder
	# named after the type of inter-rater mismatch.
	if os.path.exists(start_dir):	
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		shutil.move(start_dir,out_dir)
		
	