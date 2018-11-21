# palate getter function - averages all palate traces in ET output .con file
# outputs a text file that can be used in ssanova_palate.R
# usage: python palate-getter.py [directory name]
#	where directory contains multiple subjects' palate-finding dirs
#	target files MUST end in "palates.con"

import os, sys, argparse
from csv import reader
from numpy import mean

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
args = parser.parse_args()

try:
	expdir = args.directory
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

for root, dirs, files in os.walk(expdir):
	for con in files:

		if not 'palates.con' in con.lower():
			continue

		out_file = os.path.splitext(con)[0] + "-out.txt"

		# reads all frames from a .con file and averages; gets palate
		with open(os.path.join(root,con), 'r') as cn:
			csvreader = reader(cn, delimiter="\t")
			dat = list(csvreader)
			nframes = len(dat[0]) # get number of frames from first row
			rows = sum(1 for row in dat) # rows = 100, generally
			with open(out_file, 'w') as out:
				out.write('X' + '\t' + 'Y' + '\n') # header
				for row in dat: # go through by point in contour:
					row_floats = [float(x.strip()) for x in row if x] # change type, filter out empty strings
					x_avg = mean(row_floats[0::2])
					y_avg = mean(row_floats[1::2])
					y_avg = -y_avg # because ssanova data comes out inverted; has to match
					out_row = '\t'.join([str(round(x_avg,2)), str(round(y_avg,2))]) + '\n'
					out.write(out_row)