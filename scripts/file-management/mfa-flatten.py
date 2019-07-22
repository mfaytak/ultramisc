# Simple utility to copy audio data recorded with ultrasound to
#   to a flat directory structure with appropriate file extensions,
#   as expected by the Montreal Forced Aligner.
# Usage: python mfa-flatten.py [expdir]
#   expdir - top-level directory for one subject, as output by EchoB/Micro.

import argparse
import glob
import os
import shutil

# parse argument(s)
parser = argparse.ArgumentParser()
# read things in
parser.add_argument("expdir", 
					help="Experiment directory containing \
						acquisitions in flat structure"
					)
args = parser.parse_args()

expdir = args.expdir

glob_regexp = os.path.join(expdir,"*","*.raw")

# make new folder
alignment_in = os.path.join(expdir,"_align")
os.makedirs(alignment_in)

for rawh in glob.glob(glob_regexp):
    timestamp = os.path.split(os.path.splitext(rawh)[0])[1]
    parent = os.path.split(rawh)[0]
    wav = os.path.join(parent, str(timestamp + ".ch1.wav"))
    transcript = os.path.join(parent,"transcript.txt")
    if not os.path.exists(transcript):
        continue
    # make a new file handle for the transcript file
    if os.path.splitext(transcript)[0] != timestamp: # keeping this comparison for the future
        transcript_dst = os.path.join(alignment_in, str(timestamp + ".ch1.lab"))
    else:
        transcript_dst = os.path.join(alignment_in, transcript)
    wav_dst = os.path.join(alignment_in, str(timestamp + ".ch1.wav"))

    # transfer the files to a new folder
    shutil.copy(wav, wav_dst)
    shutil.copy(transcript, transcript_dst)
