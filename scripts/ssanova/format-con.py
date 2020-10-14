#/usr/bin/env python

'''
format-con.py: Extract pairs of columns from EdgeTrak-produced .con files 
to generate CSV files that Jeff Mielke's tongue_ssanova.R can operate on.
Extracts single target frames but can be extended to sequences.
Usage
  $ python format-con.py dirname
Arguments
  directory  dir containing all files described below
Assumptions:
1. Each acquisition (consisting of audio, ultrasound images, a TextGrid, a frame synchronization file, and a .con file output from EdgeTrak) is in a separate subdirectory in the session directory.
2. Speaker ID is given before an underscore in the top-level directory name (i.e., /.../SUBJECT_* is called as directory and fed into basedir).
3. Specific formatting requirements for files (which you may need to alter):
	frame synchronization TextGrid with extention .sync.TextGrid (frame acquisition times w.r.t. an associated audio recording)
	some number of .bmp ultrasound frame files *.###.bmp, where ### is a frame number
'''

# Authors: Matthew Faytak (faytak@ucla.edu) Copyright (c) 2015
# Last modified 10-2020

import audiolabel
import glob
import os, sys, re

from csv import reader
from ultramisc.ebutils import read_stimfile

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Experiment directory containing all subjects")
args = parser.parse_args()

basedir = args.directory
if not os.path.exists(basedir):
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

out_file = os.path.join(basedir, os.path.split(basedir)[-1] + "_cons.txt")

# generate header of output file
# this is for a particular project's metadata, but can be retooled
head = '\t'.join(["speaker","acq","token","frameIdx","vowel","X","Y"])
with open(out_file, "w") as out:
	out.write(head + "\n")

# find speaker
spkr = "S" + re.sub("[^0-9]", "", basedir)

# project-specific grouping of stimuli
low_set = ["baodian","paoxie","daoyan",
       "taoyuan","gaojian","kaojuan"]

# below on line 96, we search for any label on an otherwise empty tier.
# if running directly on forced aligner output, you can search for 
# a set of labels like so:
# vow = re.compile("^(AE1|IY1|UW1|OW1|UH1)")
# then search for "vow" (see lines 97-98)

# generate the rest of the output file
# search over .con files in first layer of subdirs
glob_exp = os.path.join(basedir,"*","*.con")
token_ct = []

for con in glob.glob(glob_exp):
    parent = os.path.dirname(con)
    basename = os.path.split(parent)[1]

    # get TGs
    tg = os.path.join(parent,str(basename + ".ch1.TextGrid"))
    sync_tg = os.path.join(parent,str(basename + ".sync.TextGrid"))

    # get stimulus; other metadata
    stimfile = os.path.join(parent,"stim.txt")
    stim = read_stimfile(stimfile)
    if stim in low_set:
        tone = "low"
    else:
        tone = "high"

    # get condition ("ba"/"init"), place, aspiration (in that order in md)
    # replace with your own metadata as needed
    md = os.path.join(parent,"meta.txt")
    with open(md) as csvfile:
        meta = reader(csvfile, delimiter="\t")
        tbl = [row for row in meta] # a little janky but works
        condition = tbl[1][0]
        place = tbl[1][1]
        aspiration = tbl[1][2]

    # instantiate audio TG handler; get release time and phone label
    # assumes one labeled interval on the searched tier
    pm = audiolabel.LabelManager(from_file=tg, from_type='praat')
    clos = pm.tier('closure').search(".", return_match=True)[0][0]
    # alternately, search for a set: (see lines 56-60)
    # v = pm.tier('segments').search(vow, return_match=True)[0][0]
    release_time = clos.t2
    phone = clos.text
    
    # get token number
    token_ct.append(phone)
    token = token_ct.count(phone)
    
    # instantiate sync TG handler; get absolute index of frame
    sc = audiolabel.LabelManager(from_file=sync_tg, from_type='praat')
    release_idx = sc.tier('pulse_idx').label_at(release_time).text
    abs_fr_idx = int(release_idx) - 1 # should yield 121 for first file
    
    # get index of first extracted frame
    bmp_list = glob.glob(os.path.join(parent,'*.bmp'))
    fr_idx = []
    for bmp in bmp_list:
        fr_num = re.search('.(\d+).bmp$',bmp)
        fr_idx.append(int(fr_num.group(1))) 
        # the int is crucial here: otherwise, min list idx (b/c list of strings!) will be returned
    first_fr = min(fr_idx)
    
    # get frame index relative to extracted frames, = column number in .con file
    col_n = abs_fr_idx - first_fr 

    # pull the appropriate columns from .con file and save to CSV
    with open(con) as conf:
        with open(out_file,"a") as out:
            csvreader = reader(conf, delimiter="\t")
            d = list(csvreader)
            rows = sum(1 for row in d) # rows = 100, generally
            x_col = (2*col_n)-2
            y_col = (2*col_n)-1
            for t in range(0,rows):
                try:
                    x_val = d[t][x_col]
                    y_val = d[t][y_col]
                except IndexError:
                    print("WARNING: some problem accessing {}):".format(con_file))
                    sys.exit(2)
                
                row_out = '\t'.join([
                    spkr,
                    basename, str(token),
                    str(abs_fr_idx),
                    condition,
                    phone, place, aspiration, tone,
                    x_val, y_val
                ])
                
                out.write(row_out + "\n")
