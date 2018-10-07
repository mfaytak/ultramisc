#/usr/bin/env python

'''
ssanova-formatter.py: Extract pairs of columns from EdgeTrak-produced .con files 
to generate CSV files that Jeff Mielke's tongue_ssanova.R can operate on.
Extracts only the center frame in a sequence.

Usage
  $ python ssanova-formatter.py dirname > [output file]

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
# Last modified 10-2018

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

# define relevant vowel labels; change as required
vow = re.compile("^(UW1|UH1)")

# generate header of output file
head = '\t'.join(["speaker","acq","token","ctrFrame","vowel","X","Y"])
print(head) # TODO write to a file instead

# find speaker; initialize token counter list
spkr = os.path.basename(basedir).split('_')[0]
token_ct = []

# generate the rest of the output file
for dirs, subdirs, files in os.walk(basedir):
	for textgrid in files:

		if not '.textgrid' in textgrid.lower():
			continue

		# .con file
		basename = textgrid.split('.')[0] # may not be general enough
		con_file = os.path.join(dirs,str(basename + '.con'))

		# .sync.txt file into a list
		sync = os.path.join(dirs,str(basename + '.bpr.sync.txt'))
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
			fr_idx.append(fr_num.group(1))
		first_fr = min(fr_idx)
		
		# instantiate LabelManager
		pm = audiolabel.LabelManager(from_file=os.path.join(dirs,textgrid), from_type='praat')

		# for all relevant vowel intervals
		for v,m in pm.tier('phone').search(vow, return_match=True):
			
			# collect word/type information and adjust token count
			stim_v = v.text
			token_ct.append(stim_v)
			token = token_ct.count(stim_v)

			# find frame number corresponding to center of C in textgrid
			v_midpoint = v.center
			diff_list = []
			for s in sync_lines:
				diff_list.append(abs(v_midpoint - s))
			ctr_match = min(enumerate(diff_list), key=itemgetter(1))[0]
			# TODO: fix this; apparently values of ctr_match = 100 cause Y coord. to not show up ???
			
			# translate center frame numer into an index for pairs of columns in .con file	
			col_n = ctr_match - int(first_fr) # TODO if ctr_match == 100, then col_n = 100-first_fr

			# locate .con file and extract X, Y using index defined in col_n; print entire array
			with open(con_file) as con:
				csvreader = reader(con, delimiter="\t")
				d = list(csvreader)
				rows = sum(1 for row in d) # TODO rows = 100, generally
				for t in range(0,rows):
					x_val =  d[t][(2*col_n)-2]
					y_val =  d[t][(2*col_n)-1]
					row_out = '\t'.join([spkr,basename,str(token),str(ctr_match),stim_v,x_val,y_val])
					print(row_out)
