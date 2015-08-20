#!/usr/bin/env python

# import modules
from shutil import copyfile
from numpy.ma import masked_where
from netCDF4 import Dataset as nc
from optparse import OptionParser

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.mask.0.01.nc4", type = "string",
                  help = "Input mask netCDF file", metavar = "FILE")
parser.add_option("-c", "--countryfile", dest = "countryfile", default = "country.nc4", type = "string",
                  help = "netCDF file of countries", metavar = "FILE")
parser.add_option("-g", dest = "cgadm", default = "145", type = "int",
                  help = "GADM code of country to mask")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.mask.0.01.new.nc4", type = "string",
                  help = "Output mask netCDF file", metavar = "FILE")
options, args = parser.parse_args()

inputfile   = options.inputfile
countryfile = options.countryfile
country     = options.cgadm
outputfile  = options.outputfile

with nc(countryfile) as f:
    countries = f.variables['country'][:]

copyfile(inputfile, outputfile)
with nc(outputfile, 'a') as f:
    mask    = f.variables['mask']
    maskvar = mask[:]
    maskvar = masked_where(countries == country, maskvar)
    mask[:] = maskvar