#/usr/bin/env python

'''
ssanova-formatter.py: Extract pairs of columns from EdgeTrak-produced .con files 
to generate CSV files that Jeff Mielke's tongue_ssanova.R can operate on.
Extracts only the center frame in a sequence.
Usage
  $ python ssanova-formatter.py dirname > [output file].txt
Arguments
  dirname  dir containing all files described below
Requirements for a well-formatted output:
1. Each acquisition (consisting of audio, ultrasound images, a TextGrid, a frame synchronization file, and a .con file output from EdgeTrak) is in a separate subdirectory in the parent directory.
2. Speaker ID is given before an underscore in the top-level directory name (i.e., /.../SUBJECT_* is called as dirname and fed into basedir).
3. Specific formatting requirements for files (which you may need to alter):
	frame synchronization file with extention .sync.txt file (list of frame acquisition times w.r.t. an associated audio recording)
	some number of .bmp ultrasound frame files *.###.bmp, where ### is a frame number consisting of any number of [0-9]
'''

# Authors: Matthew Faytak (faytak@ucla.edu) Copyright (c) 2015
# Last modified 11-2018

import os, sys, re, glob
import audiolabel
from csv import reader
from operator import itemgetter

# TODO use argument parser for better options
def usage():
	print(sys.exit(__doc__))

try:
	basedir = os.path.abspath(sys.argv[1])
except IndexError:
	usage()
	sys.exit(2)

out_file = os.path.join(basedir, os.path.split(basedir)[-1] + "_cons.txt")

# generate header of output file
head = '\t'.join(["speaker","acq","token","ctrFrame","vowel","X","Y"])
with open(out_file, "w") as out:
	out.write(head + "\n")

# define relevant vowel labels; change as required
vow = re.compile("^(AE1|IY1|UW1|OW1|UH1)")

# find speaker; initialize token counter list
spkr = "S" + re.sub("[^0-9]", "", basedir)
token_ct = []

# generate the rest of the output file
for dirs, subdirs, files in os.walk(basedir):
	for textgrid in files:

		if not '.ch1.textgrid' in textgrid.lower():
			continue

		# get the support file names
		if 'bpr' in textgrid.lower():
			basename = textgrid.split('.')[0] + '.bpr'
		else:
			basename = textgrid.split('.')[0]
		
		con_file = os.path.join(dirs, str(basename + '.con'))
		con_file = con_file.replace('.bpr', '')

		# .sync.txt file into a list
		sync = os.path.join(dirs, str(basename + '.sync.txt'))
		sync_lines = []
		with open(sync, 'r') as s:
			for line in s:
				try:
					sync_lines.append(float(line.strip().split("\t")[0]))
				except ValueError:
					pass # ignore line if a header is present

		# get first frame index
		bmp_list = glob.glob(os.path.join(dirs,'*.bmp'))
		fr_idx = []
		for bmp in bmp_list:
			fr_num = re.search('.(\d+).bmp$',bmp)
			fr_idx.append(int(fr_num.group(1))) # the int is crucial here: otherwise, min list idx (b/c list of strings!) will be returned
		first_fr = min(fr_idx)
		last_fr = max(fr_idx)
		
		# instantiate LabelManager
		pm = audiolabel.LabelManager(from_file=os.path.join(dirs,textgrid), from_type='praat')

		# for all relevant vowel intervals
		for v,m in pm.tier(0).search(vow, return_match=True):
			
			# skip any tokens from non-target words
			pron = pm.tier(1).label_at(v.center).text
			if pron not in ["BUH", "FUH", "BUW", "BOOW", "BAAE", "BIY"]:
				continue
			# correct UH1 vowel depending on pronunciation FUH or BUH
			elif pron == "FUH": # TODO handle occasional FUW
				phone = "VU"
			elif pron == "BUH":
				phone = "BU"
			elif pron == "BOOW":
				phone = "UW"
			else:
				phone = v.text.replace('1','')

			# collect word/type information and adjust token count
			token_ct.append(phone)
			token = token_ct.count(phone)

			# find frame number corresponding to center of C in textgrid
			v_midpoint = v.center
			diff_list = []
			for s in sync_lines:
				diff_list.append(abs(v_midpoint - s))
			ctr_match = min(enumerate(diff_list), key=itemgetter(1))[0] # ctr_match is 77, which is not in range at all
			
			# check to ensure that it's within the recording window
			if first_fr > ctr_match or last_fr < ctr_match:
				print("WARNING ({}):".format(con_file))
				print("\t target at frame {} is outside of extracted frames; skipping.".format(ctr_match))
				print("\tIf there is a double production, disregard this warning.")
				continue

			# translate center frame numer into an index for pairs of columns in .con file	
			col_n = ctr_match - first_fr 

			# locate .con file and extract X, Y using index defined in col_n; print entire array
			with open(con_file) as con:
				with open(out_file,"a") as out:
					csvreader = reader(con, delimiter="\t")
					d = list(csvreader)
					rows = sum(1 for row in d) # TODO rows = 100, generally

					x_col = (2*col_n)-2
					y_col = (2*col_n)-1

					for t in range(0,rows):
						try:
							x_val = d[t][x_col]
							y_val = d[t][y_col]
						except IndexError:
							print("WARNING: other problem accessing {}):".format(con_file))
							sys.exit(2)
					
						row_out = '\t'.join([spkr,basename,str(token),str(ctr_match),phone,x_val,y_val])
						out.write(row_out + "\n")