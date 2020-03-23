import os
from unicodedata import normalize

def read_echob_metadata(rawfile):
    '''
    Gather information about a .raw file from its .img.txt file. 
    For legacy .raw data without a header; if a header exists,
    use ultratils utilities.
    Inputs: a .raw file, which is assumed to have an .img.txt file
      with the same base name.
    Outputs:
      nscanlines, the number of scan lines ("width" of unconverted img)
      npoints, the number of pixels in each scan line ("height" of img)
      not_junk, the pixel index in each scan line where junk data begins
    '''
    mfile = os.path.splitext(rawfile)[0] + ".img.txt"
    mdict = {}
    with open(mfile, 'r') as mf:
        k = mf.readline().strip().split("\t")
        v = mf.readline().strip().split("\t")
        for fld,val in zip(k, v):
            mdict[fld] = int(val)
    
    nscanlines = mdict['Height']
    npoints = mdict['Pitch']
    junk = npoints - mdict['Width'] # number of rows of junk data at outer edge of array
    
    return nscanlines, npoints, junk

def _deaccent(mystr):
    '''
    Convert string to standardized bytes object and return 
      decoded string without any accented characters to 
      facilitate item comparison.
    '''
    strip_bytes = normalize('NFC', mystr).encode('ascii','ignore')
    string_back = strip_bytes.decode('utf-8')

    return string_back


def read_stimfile(stimfile, deaccent=False):
    '''
    Read plaintext stim.txt file; return stim as string. 
    Cleanup using _deaccent() optional.
    '''
    with open(stimfile, "r") as stfile:
        stim = stfile.read().rstrip('\n')

    if deaccent:
        stim = _deaccent(stim)

    return stim

def read_listfile(listfile, deaccent=False):
    '''
    Read stimulus list file (for subsetting, naming 
      distractors, etc.) and return plaintext list.
    Cleanup using _deaccent() optional.
    '''
    with open(listfile, "r") as lfile:
        outlist = lfile.read().splitlines()

    if deaccent:
        outlist = [_deaccent(l) for l in outlist]

    return outlist

