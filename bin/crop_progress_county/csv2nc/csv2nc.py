#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from numpy import ones, zeros
from optparse import OptionParser
from numpy.ma import masked_array
from netCDF4 import Dataset as nc
from CountyDistances import CountyDistances
from CropProgressCounty import CropProgressData

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--infile", dest = "infile", default = "", type = "string",
                  help = "Input CSV file", metavar = "FILE")
parser.add_option("-d", "--cdfile", dest = "cdfile", default = "", type = "string",
                  help = "County distances CSV file", metavar = "FILE")
parser.add_option("-o", "--outfile", dest = "outfile", default = "", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

infile  = options.infile
cdfile  = options.cdfile
outfile = options.outfile

if not os.stat(infile).st_size:
    print 'File %s is empty. Exiting . . .' % infile
    sys.exit()

cdobj = CountyDistances(cdfile) # load county distances

cp = CropProgressData(infile, cdobj) # run parser

nvars, ncounties = len(cp.vars), len(cp.counties)

var = masked_array(zeros((nvars, ncounties)), mask = ones((nvars, ncounties)))
for i in range(nvars):
    var[i] = cp.getVar(cp.vars[i])

with nc(outfile, 'w') as f:
    f.createDimension('var', nvars)
    vvar = f.createVariable('var', 'i4', 'var')
    vvar[:] = range(1, nvars + 1)
    vvar.units = 'mapping'
    vvar.long_name = ', '.join(cp.vars)

    f.createDimension('day', 1)
    dayvar = f.createVariable('day', 'i4', 'day')
    dayvar[:] = cp.day
    dayvar.units = 'YYYYDDD'
    dayvar.long_name = 'time'

    f.createDimension('county', ncounties)
    countyvar = f.createVariable('county', 'f8', 'county')
    countyvar[:] = cp.counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'

    datavar = f.createVariable('data', 'f4', ('var', 'day', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    datavar[:] = var