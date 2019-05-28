from ultramisc.utils.ebutils import read_echob_metadata, read_stimfile
from ultratils.rawreader import RawReader
from ultratils.pysonix.scanconvert import Converter
import imgphon.imgphon.ultrasound as us
from PIL import Image # check if configured on VM
import audiolabel # need to download too - GH
import os, glob, subprocess
import numpy as np
from operator import itemgetter
import argparse

# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument("expdir", 
					help="Experiment directory containing all subjects'\
						  caches and metadata in separate folders"
					)
parser.add_argument("-f", 
					"--flop", 
					help="Horizontally flip the data", 
					action="store_true"
					)
args = parser.parse_args()

expdir = args.expdir
rawfile_glob_exp = os.path.join(expdir,"*","*.raw")

class Header(object):
	def __init__(self):
		pass
class Probe(object):
	def __init__(self):
		pass

conv = None

for rf in glob.glob(rawfile_glob_exp):
	parent = os.path.dirname(rf)
	basename = os.path.split(parent)[1]

	# use stim.txt to skip non-trials, flap.txt to skip words without flaps
	stimfile = os.path.join(parent,"stim.txt")
	stim = read_stimfile(stimfile)
	if stim == "bolus" or stim == "practice":
		continue
	flapfile = os.path.join(parent,"flap.txt")
	flap_set = read_stimfile(flapfile)
	if flap_set == "N":
		continue

	if conv is None:
		print("Making converter...")
		nscanlines, npoints, junk = read_echob_metadata(rf)
		header = Header()
		header.w = nscanlines       # input image width
		header.h = npoints - junk   # input image height, trimmed
		header.sf = 4000000         # magic number, sorry!
		probe = Probe()
		probe.radius = 10000        # based on '10' in transducer model number
		probe.numElements = 128     # based on '128' in transducer model number
		probe.pitch = 185           # based on Ultrasonix C9-5/10 transducer
		conv = Converter(header, probe)
	
	print("Now working on {}".format(parent))
	rdr = RawReader(rf, nscanlines=nscanlines, npoints=npoints)
	
	wav = os.path.join(parent,str(basename + ".ch1.wav"))
	tg = os.path.join(parent,str(basename + ".ch1.TextGrid"))
	sync_tg = os.path.join(parent,str(basename + ".sync.TextGrid"))
	sync = os.path.join(parent,str(basename + '.sync.txt'))
	idx_txt = os.path.join(parent,str(basename + ".idx.txt"))
	
	# instantiate LabelManager objects for FA transcript and sync pulses
	try: 
		pm = audiolabel.LabelManager(from_file=tg, from_type="praat")
	except FileNotFoundError:
		print("No alignment TG in {}; skipping".format(basename))
		continue

	try: 
		sync_pm = audiolabel.LabelManager(from_file=sync_tg, from_type="praat")
	except FileNotFoundError:
		print("No sync TG in {}; skipping".format(basename))
		continue
		
	# search for target words in 'words' tier
	for wd in pm.tier('words'):
		if not wd.text: # skip intervals in which no word was found
			continue
		if wd.text.lower() != stim.lower():
			# fix for multi-word stimuli:
			if wd.text.lower() in ['heard', 'bird', 'hard']:
				# take next word's .t2 as word_t2
				# as in "heard of it", "bird of paradise", "hard of hearing"
				word_t1 = wd.t1
				word_t2 = pm.tier('words').next(wd).t2 # invariably "of"
			elif wd.text.lower() == 'carta':
				# take 'carta' even though it doesn't match any stim (which is Magna Carta for this one)
				word_t1 = wd.t1
				word_t2 = wd.t2
			else: 
				continue
		else:
			word_t1 = wd.t1
			word_t2 = wd.t2

		for ph in pm.tier('phones'):
			if ph.t1 < word_t1:
				continue
			if ph.t2 > word_t2:
				continue
			if ph.text.upper() not in ["T", "D"]:
				continue
			# TODO check if no flap found, issue warning
			before = pm.tier('phones').prev(ph)
			if before.text.upper() == "R": # if there's a postvocalic R, then go back an additional interval
				before = pm.tier('phones').prev(before)
			after = pm.tier('phones').next(ph)
			
			print("Extracting {} {} {} from {}".format(before.text, ph.text, after.text, stim))

			start_flap = ph.t1
			end_flap = ph.t2
			start_time = before.t1
			end_time = after.t2
			
			# TODO set from here down as fcn? args t1, t2
			# options: highlight=['TX','DX'], fast/slow/both
			# then script finds times
			# then it extracts images
			# then it runs ffmpeg
 
			diff_start = []
			diff_end = []
			diff_start_flap = []
			diff_end_flap = []
			
			for frame in sync_pm.tier('pulse_idx'):
				diff_s = abs(frame.center - start_time)
				diff_start.append(diff_s)
				diff_e = abs(frame.center - end_time)
				diff_end.append(diff_e)
				diff_sf = abs(frame.center - start_flap)
				diff_start_flap.append(diff_sf)
				diff_ef = abs(frame.center - end_flap)
				diff_end_flap.append(diff_ef)

			# get start/end indices; flap indices
			start_idx = min(enumerate(diff_start), key=itemgetter(1))[0] - 1
			end_idx = min(enumerate(diff_end), key=itemgetter(1))[0] - 1
			start_flap_idx = min(enumerate(diff_start_flap), key=itemgetter(1))[0] - 1
			end_flap_idx = min(enumerate(diff_end_flap), key=itemgetter(1))[0] - 1
			
			# make sure there are at least 20 frames after end of flap
			# credit: Jennifer Kuo
			if (end_idx - end_flap_idx) < 15: 
				end_idx = 15 + end_flap_idx

			# get set of indices for timing of flap
			is_flap = list(range(start_flap_idx, end_flap_idx))
			is_flap = [ix - start_idx for ix in is_flap]
			
			# get frames using RawReader's reader object
			target_frames = rdr.data[start_idx:end_idx]
			
			for idx,fr in enumerate(target_frames):

				# trim junk pixels off of top
				trimmed_frame = fr[junk:,:]

				# convert to fan shape
				conv_frame = conv.convert(np.flipud(trimmed_frame))
				messy_frame = np.flipud(conv_frame)
				
				norm_frame = us.normalize(messy_frame)
				cframe = us.clean_frame(norm_frame, median_radius=15, log_sigma=4)
				
				pre_final_frame = (cframe*255).astype(np.uint8)
				
				# reverse if needed
				if args.flop:
					final_frame = np.fliplr(pre_final_frame)
				else:
					final_frame = np.copy(pre_final_frame)
				
				# if frame occurs during flap, add a signal
				if idx in is_flap:
					final_frame[10:80, -80:-10] = 255

				# create frame handle and save to copy dir
				fh = basename + "." + "{0:05d}".format(idx+1) + ".bmp"
				out_img = Image.fromarray(final_frame)
				out_img.save(os.path.join(fh))

			frame_exp = os.path.join(basename + ".%05d.bmp")

			out_fh = basename + '_slow.avi'
			out_path = os.path.join(parent, out_fh)
			avi_args = ['ffmpeg', 
							'-loglevel', 'panic',
							'-y',
							'-framerate', '4', # values that work here include 4, 12.5, and 25
							'-i', frame_exp,
							#'-r', str(framerate),
							'-vcodec', 'huffyuv',
							'-vf', 'scale=iw/2:ih/2',
							out_path]
			subprocess.check_call(avi_args)
			
			out_fh_fast = basename + '_fast.avi'
			out_path_fast = os.path.join(parent, out_fh_fast)
			avi_args_fast = ['ffmpeg', 
							'-loglevel', 'panic',
							'-y',
							'-framerate', '12.5', 
							'-i', frame_exp,
							#'-r', str(framerate),
							'-vcodec', 'huffyuv',
							'-vf', 'scale=iw/2:ih/2',
							out_path_fast]
			subprocess.check_call(avi_args_fast)

			# delete the .bmp files once done
			for item in os.listdir("."):
				if item.endswith(".bmp"):
					os.remove(item)
