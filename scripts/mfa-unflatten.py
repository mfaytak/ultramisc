# Simple utility to "unflatten" forced alignment output from
#   the Montreal Forced Aligner (move audio files and TextGrid
#   annotations back into acquisition directories). Assumes
#   each ultrasound acquisition in its own subdirectory in expdir.
#   Assumes each .TextGrid has a matching directory name.
# Usage: python mfa-unflatten.py [tgdir] [expdir]

import os
import shutil
import argparse

# parse argument(s)
parser = argparse.ArgumentParser()
# read things in
#parser.add_argument("wavdir", "-w", action="store",
#					help="Directory containing .wav and .lab \
#					files in flat structure; input to MFA"
#					)
parser.add_argument("tgdir", action="store",
					help="Directory containing alignment \
					    TextGrids output by MFA"
					)
parser.add_argument("expdir", action="store",
					help="Experiment directory containing \
						ultrasound acquisitions in flat structure; \
						destination of TextGrid files."
					)
args = parser.parse_args()

tgdir = args.tgdir
expdir = args.expdir

for dirs,subdirs,textgrids in os.walk(tgdir):
    for tg in textgrids:
        tgh = os.path.join(os.path.abspath(dirs),tg)
        if tg == "unaligned.txt":
            with open(tgh, "r") as un:
                print("WARNING: SOME SOUND FILES NOT ALIGNED")
                lines = [line.rstrip('\n') for line in un]
                for line in lines:
                    print(line)
            continue
        timestamp = tg.replace(".ch1.TextGrid","")
        dest = os.path.join(expdir,timestamp)
        shutil.copy(tgh, dest)