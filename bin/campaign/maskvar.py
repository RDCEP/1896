#!/usr/bin/env python

# import modules
from shutil import copyfile
from numpy.ma import masked_where
from netCDF4 import Dataset as nc
from optparse import OptionParser

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile1", dest = "inputfile", default = "Campaign.nc4", type = "string",
                  help = "Input file", metavar = "FILE")
parser.add_option("--v1", dest = "v1", default = "date_1", type = "string",
                  help = "Mask variable")
parser.add_option("--v2", dest = "v2", default = "scale_p1", type = "string",
                  help = "Variable to modify")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.masked.nc4", type = "string",
                  help = "Output file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
v1         = options.v1
v2         = options.v2
outputfile = options.outputfile

with nc(inputfile) as f:
    v1arr = f.variables[v1][:]
    v2arr = f.variables[v2][:]

v2arr = masked_where(v1arr.mask, v2arr)

copyfile(inputfile, outputfile)
with nc(outputfile, 'a') as f:
    v2var = f.variables[v2]
    v2var[:] = v2arr