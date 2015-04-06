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
from CropProgressCountyDBF import CropProgressDataDBF

parser = OptionParser()
parser.add_option("-i", "--infile", dest = "infile", default = "", type = "string",
                  help = "Input DBF file", metavar = "FILE")
parser.add_option("-d", "--cdfile", dest = "cdfile", default = "", type = "string",
                  help = "County distances CSV file", metavar = "FILE")
parser.add_option("-o", "--outfile", dest = "outfile", default = "", type = "string",
                  help = "Output netcdf file", metavar = "FILE")
options, args = parser.parse_args()

infile  = options.infile
cdfile  = options.cdfile
outfile = options.outfile

if not os.stat(infile).st_size:
    print 'File %s is empty. Exiting . . .' % infile
    sys.exit()

if os.path.isfile(outfile):
    print 'File %s already exists. Exiting . . .' % outfile
    sys.exit()

cdobj = CountyDistances(cdfile) # load county distances

cp = CropProgressDataDBF(infile, cdobj) # run parser

nvars, ndtype, ncounties = len(cp.vars), len(cp.value), len(cp.counties)

if not nvars or not ncounties: # no data
    print 'File %s contains no data' % infile
    sys.exit()

var = masked_array(zeros((nvars, ndtype, ncounties)), mask = ones((nvars, ndtype, ncounties)))
for i in range(nvars):
    var[i] = cp.getVar(cp.vars[i])

with nc(outfile, 'w') as f:
    f.createDimension('var', nvars)
    vvar = f.createVariable('var', 'i4', 'var')
    vvar[:] = cp.vars
    vvar.long_name = 'variable'

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

    nvar = f.createVariable('ndata', 'f4', ('var', 'day', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    nvar[:] = var[:, 0, :]

    navar = f.createVariable('nadata', 'f4', ('var', 'day', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    navar[:] = var[:, 1, :]