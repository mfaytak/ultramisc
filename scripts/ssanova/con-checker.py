
# Checks whether 
# Can easily be extended to any processing task that takes place 
# in a subject directory and involves outputs of easily identifiable
# files.

# Usage: python con-checker.py [directory containing all acquisitions/data/etc]

# Authors: Matthew Faytak (faytak@ucla.edu) Copyright (c) 2018
# Last modified 11-2018

import os, sys

def usage():
	print(sys.exit(__doc__))

try:
	basedir = os.path.abspath(sys.argv[1])
except IndexError:
	usage()
	sys.exit(2)

missing_files = 0

# generate the rest of the output file
for dirs, subdirs, files in os.walk(basedir):
	for textgrid in files:

		# only check for .con files for which a .ch1.TextGrid file exists
		if not '.ch1.textgrid' in textgrid.lower():
			continue

		# get related file names
		if 'bpr' in textgrid.lower():
			basename = textgrid.split('.')[0] + '.bpr'
		else:
			basename = textgrid.split('.')[0]
		
		con_file = os.path.join(dirs, str(basename + '.con'))
		con_file = con_file.replace('.bpr', '')

		if os.path.isfile(con_file):
			continue
			# TODO check here for other files ending in .con
		else:
			print("\tNo .con file in {}".format(basename))
			missing_files += 1

		# TODO check for .con files whose basenames don't match
		#elif # another file ends in .con that isn't con_file

		# TODO check for multiple .con files

# print out some encouragement
if missing_files == 0:
	print("Congratulations, you've finished work in {}!".format(basedir))
else:
	print("Almost there! You have a total of {} missing files.".format(missing_files))

