import vlc, easygui, glob, os
from ultramisc.utils.ebutils import read_stimfile
import time
import argparse

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing all subjects'\
						  caches and metadata in separate folders"
					)
args = parser.parse_args()

try:
	expdir = args.expdir
except IndexError:
	print("\tDirectory provided doesn't exist")
	ArgumentParser.print_usage
	ArgumentParser.print_help
	sys.exit(2)

expdir = args.expdir

ann = input("Enter your initials: ")

out_file = "annotations-{}.txt".format(expdir)

avi_glob_exp = os.path.join(expdir, "*", "*_slow.avi")

# write header to file
with open(out_file, "w") as out:
	out.write('\t'.join(["acq", "stim", "before", "after", "voi", "ann", "label"]) + '\n')

# loop through available _slow.avi files
for av in glob.glob(avi_glob_exp):
    # gather metadata strings
    parent = os.path.dirname(av)
    stimfile = os.path.join(parent,"stim.txt")
    stim = read_stimfile(stimfile)
    beforefile = os.path.join(parent,"before.txt")
    before = read_stimfile(beforefile)
    afterfile = os.path.join(parent,"after.txt")
    after = read_stimfile(afterfile)
    voicefile = os.path.join(parent,"voice.txt")
    voice = read_stimfile(voicefile)
    
    # find the faster AVI file
    basename = os.path.split(parent)[1]
    av_fast = os.path.join(parent,str(basename + "_fast.avi"))

        # TODO add name to player
    while True:
        click = easygui.buttonbox(title="Playing {}".format(av),msg="Press Play to start",choices=["Play", "Play fast", "Label"])
        #print(choice)
        if click == "Play":
            player = vlc.MediaPlayer(av)
            player.play()
            time.sleep(5)
            player.stop()
        elif click == "Play fast":
            player = vlc.MediaPlayer(av_fast)
            player.play()
            time.sleep(2)
            player.stop()
        elif click == "Label":
            choice = easygui.buttonbox(title="Select the best label", choices=["up_flap", "down_flap", "low_tap", "high_tap"])
            with open(out_file, "a") as out:
                out.write('\t'.join([basename, stim, before, after, voice, ann, choice]) + '\n')
            break
        else:
            choice = "NA"
            with open(out_file, "a") as out:
                out.write('\t'.join([basename, stim, before, after, voice, ann, choice]) + '\n')
            break 
