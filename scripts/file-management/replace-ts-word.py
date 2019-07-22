'''
replace-ts-word: find and replace words in transcript files.
  Intended use is changing spellings to get along with forced alignment
  dictionaries.
'''

import os, sys, glob
import argparse

def read_transcript(my_ts_file):
	with open(my_ts_file, "r") as tsfile:
		sentence = tsfile.read().rstrip('\n')
		wordlist = sentence.split()
	return wordlist

# parse argument(s)
parser = argparse.ArgumentParser()
# read things in
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
parser.add_argument("-p", "--problem", 
					help="Word in transcripts to be changed"
					)
parser.add_argument("-s", "--sub", 
					help="What to change the word to"
					)
# pull them together, making an "args" object with 3 attributes
# args.expdir, args.word, args.sub
args = parser.parse_args()
if args.problem is None or args.sub is None:
	print("Problem word and/or substitution undefined; exiting.")
	sys.exit()

# figure out where all .raw files are
expdir = os.path.normpath(args.expdir)
glob_regex = os.path.join(os.path.normpath(args.expdir), # our subject dir
						  "*", # wildcard (any directory)
						  "*.raw" # wildcard (any filename) plus .raw
						 )

# running glob.glob gives us a list of filepaths matching the regexp above
# and we iterate through this list, finding all ts files
for rf in glob.glob(glob_regex):
	parent = os.path.dirname(rf)
	tsfile = os.path.join(parent,"transcript.txt")
	if os.path.exists(tsfile):
		ts_list = read_transcript(tsfile)
		print(ts_list)
		# Python time! expressions like this are called 
		# "list comprehensions" and work fine in Python.
		# see second answer to this question: 
		# https://stackoverflow.com/questions/2582138/finding-and-replacing-elements-in-a-list-python
		#print(args.problem in ts_list)
		mod_ts_list = [args.sub if wd==args.problem else wd for wd in ts_list]
		print(mod_ts_list)
		with open(tsfile, "w") as ts:
			ts.write(' '.join(mod_ts_list))
	else:
		continue
