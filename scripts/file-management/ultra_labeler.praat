## Description of the script labeler.praat
# This script goes through all of the .wav sound files in sound_folder; for each file, the script will check to 
# see whether there is a textgrid with the same name in textgrid_folder. If there is one, the script will read that textgrid 
# in; if there is not, the script will create a textgrid with the tiers you have specified. As it goes through the files, it 
# will take the sound file and its textgrid (either existing or newly made) and put them into the Editor for you so that you 
# can add information to the textgrid. While you are working in the Editor window, there will be a little window up with 
# buttons "Continue" and "Stop". When you are done with a file, click the "Continue" button and the script will move on to the 
# next file.
## End of description

# When you run the script, a form will appear that asks you to fill in the name of the folder where your sound files are, 
# an initial sub-string that all the files you want to work on now share (this is optional -- if you don't fill anything in 
# here, the script will go through all the sound files), the folder where you want to save the textgrids (or where your 
# existing textgrids are), the tiers you want in your new textgrids, and which of those tiers you want to be point tiers.

form Select directories and tiers
	sentence sound_folder 
	sentence initial_string 
        sentence textgrid_folder 
        sentence tiers 
        sentence point_tiers 
endform

# Before it does anything else, the script checks to see whether the last character in sound_folder and textgrid_folder 
# is a backslash or a front slash. If the last character is neither of these, the script will add a final backslash 
# to the end of the folder name. If you use an unusual operating system and neither the backslash or the forward slash 
# is an acceptable directory separator, you can take this part of the script out of your copy and make sure that the 
# correct separator character is at the end of the folder names by hand, in the form.

sound_folder_check$ = right$ (sound_folder$, 1)
if sound_folder_check$ <> "\" and sound_folder_check$ <> "/"
   sound_folder$ = sound_folder$ + "\"
endif

textgrid_folder_check$ = right$ (textgrid_folder$, 1)
if textgrid_folder_check$ <> "\" and textgrid_folder_check$ <> "/"
   textgrid_folder$ = textgrid_folder$ + "\"
endif

# Now, the script makes a list of all the .wav sound files in the folder where you've told it to look for sound files. If 
# you entered something in the field "initial_string", the list will include only .wav files whose names start with that 
# string. If you left "initial_string" blank, it will list all the .wav files.

Create Strings as file list... list 'sound_folder$''initial_string$'*.wav
file_count = Get number of strings

# Loop through files and make grids (this section partly inspired by code by Katherine Crosswhite, with fixes for ultrasound
# data made by Matt Faytak). The script goes through the list it made. This little chunk gets a single sound file and makes 
# a variable object_name$ that is the name of the sound file but with the file extension stripped off. Another variable dot_filename$
# is created to double-check for a file name variant often encountered when data was recorded using the ultrasound.

for k from 1 to file_count
     select Strings list
     current$ = Get string... k
     Read from file... 'sound_folder$''current$'
     object_name$ = selected$ ("Sound")
     dot_filename$ = replace$ (object_name$, "_ch1", ".ch1", 1)

# Below: look for a textgrid in the textgrid folder. If found, open it, otherwise make new one. An existing textgrid will 
# not be changed by the script at all. A new textgrid will have the tiers you listed in the tiers field. The tier names that 
# were also in the point_tiers field will be point tiers; the others will be interval tiers.
# This section inspired by code by Jen Hay (more ultrasound-related fixes by Matt Faytak).

# At the end of the last block, the textgrid was selected but the sound wasn't. The script now selects the sound, as well, 
# and then puts the sound and textgrid into the Editor together. Then the script pauses and puts up the window with buttons 
# that lets you tell it when you want to continue. Once the Editor comes up, the script won't do anything until you press 
# "Continue" in that little window. Once you do hit "Continue," the script will save the textgrid and then remove the 
# sound and textgrid that you were just working on. Next, it will move on to the next sound file in the list.

     grid_name$ = "'textgrid_folder$''object_name$'.TextGrid"
     dot_grid_name$ = "'textgrid_folder$''dot_filename$'.TextGrid"
     if fileReadable (grid_name$)
  	Read from file... 'grid_name$'
  	Rename... 'object_name$'
        plus Sound 'object_name$'
        Edit
        pause Annotate tiers, then press continue...
        minus Sound 'object_name$'
        Write to text file... 'textgrid_folder$''object_name$'.TextGrid
     elsif fileReadable (dot_grid_name$)
  	Read from file... 'dot_grid_name$'
  	Rename... 'object_name$'
        plus Sound 'object_name$'
        Edit
        pause Annotate tiers, then press continue...
        minus Sound 'object_name$'
        Write to text file... 'textgrid_folder$''dot_filename$'.TextGrid
     else
  	select Sound 'object_name$'
  	To TextGrid... "'tiers$'" 'point_tiers$'
        plus Sound 'object_name$'
        Edit
        pause Annotate tiers, then press continue...
        minus Sound 'object_name$'
        Write to text file... 'textgrid_folder$''object_name$'.TextGrid
     endif

# End Jen Hay inspired block

     select all
     minus Strings list
     Remove
endfor

# When the script has gone through all the files in the list it made, it will remove the list from the object window and 
# then it will bring up the Praat info window with a little text in it that lets you know how many files you just annotated.

select Strings list
Remove
clearinfo
echo Done. 'file_count' files annotated.

# This script was written by Kevin Ryan 9/05 and has been modified for use in Ling 104. Some parts of the script were 
# inspired by Katherine Crosswhite and some by Jennifer Hay. Kevin's original comments about which parts were inspired by 
# each of them have been retained.