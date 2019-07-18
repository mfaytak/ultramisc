### TAP/FLAP Project
### Python script for checking if all textgrids have been adjusted
### instructions: In command line/terminal, run python checkadjusting.py TG_DIR,
### where TG_DIR is the directory containing the textgrids.
## Packages that need to be downloaded: audiolabel

##Jennifer Kuo, July 2019

import audiolabel # need to download from github
import os, glob, re
import argparse
import numpy as np

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("expdir",
                    help="Experiment directory containing all subjects'\
                          caches and metadata in separate folders"
                    )

args = parser.parse_args()

tg_dir = args.expdir

class Header(object):
    def __init__(self):
        pass
class Probe(object):
    def __init__(self):
        pass

count = 0

## loop through all textgrids
for textgrid in os.listdir(tg_dir): 
    acq_name = str(textgrid.split('.')[0])

    tg_path = os.path.join(tg_dir,textgrid)

    if not '.ch1.textgrid' in tg_path.lower():
            continue
    pm = audiolabel.LabelManager(from_file=tg_path, from_type="praat")

    # var used to check if any 'x' was found in the target word.

    adjusted = False

    ##loop through all words in each textgrids
    for word in pm.tier('words'):
        phones = []

        #ignore frame sentence
        if (word.text in ['we','have','before','it','']):
            continue
        ## for the target word(s):
        ##get all the phones in the target word(s)
        for t in (np.arange(word.t1, word.t2, 0.01)):
            phon = pm.tier('phones').label_at(t)
            phones.append(phon)
        phones = set(phones)

        ## loop through all the phones in target word.
        for p in phones:

            ## if 'x' was found in a phone, check that it corresponds
            ## to the correct part of the target word/phrase. 
            if "x" in p.text:
                target_word = pm.tier('words').label_at(p.center).text
                if not any(s in p.text.lower() for s in ["tx","dx","rx"]):
                    print("Wrong label in Acq. " + acq_name + ". Label should be on 't', 'd', or 'r'. ")
                    count = count + 1
                if target_word == "hearing":
                    print("Wrong label in Acq. " + acq_name + ". Label should be on 'hard', not 'hearing'. ")
                    count = count + 1
                elif target_word == "paradise":
                    print("Wrong label in Acq. " + acq_name + ". Label should be on 'bird', not 'paradise'. ")
                    count = count + 1
                ## if no mistakes were found, set adjusted to True
                else:
                    adjusted = True
        ## Make note if no phones within the target item contained 'x'
        if not adjusted:
            print("Acq. " + acq_name + " was not labeled.")
            count = count + 1

## Print summary message.
if count == 0:
    print("Congratulations! You are done adjusting textgrids.")
else:
    print(str(count) + " acquisitions need to be fixed.")


