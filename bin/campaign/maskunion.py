#!/usr/bin/env python

# import modules
from shutil import copyfile
from netCDF4 import Dataset as nc
from optparse import OptionParser

# parse inputs
parser = OptionParser()
parser.add_option("--inputfile1", dest = "inputfile1", default = "maize.mask.0.01.nc4", type = "string",
                  help = "First input mask netCDF file", metavar = "FILE")
parser.add_option("--inputfile2", dest = "inputfile2", default = "all.mask.0.05.nc4", type = "string",
                  help = "Second input mask netCDF file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.all.mask.0.05.nc4", type = "string",
                  help = "Output gridlist file", metavar = "FILE")
options, args = parser.parse_args()

inputfile1 = options.inputfile1
inputfile2 = options.inputfile2
outputfile = options.outputfile

with nc(inputfile1) as f: mask1 = f.variables['mask'][:]
with nc(inputfile2) as f: mask2 = f.variables['mask'][:]

mask1[~mask2.mask] = 1

copyfile(inputfile1, outputfile)
with nc(outputfile, 'a') as f:
    mvar = f.variables['mask']
    mvar[:] = mask1