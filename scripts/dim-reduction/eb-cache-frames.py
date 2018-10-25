#!/usr/bin/env python

# TODO
# this is for Suzhou Chinese data
# change vow and the conditional flow statements accordingly

import os, re, glob, shutil
from PIL import Image
import numpy as np
import argparse
import audiolabel
from operator import itemgetter
from ultratils.rawreader import RawReader
from ultratils.pysonix.scanconvert import Converter

# TODO copy eb-pca-prep ...
# except where you take RawReader method from eb-extract-frames