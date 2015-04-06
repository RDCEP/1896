#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from os import listdir, sep
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import zeros, append, unique

parser = OptionParser()
parser.add_option("-i", "--indir", dest = "indir", default = "", type = "string",
                  help = "Input directory of files")
parser.add_option("-o", "--outfile", dest = "outfile", default = "", type = "string",
                  help = "Output netcdf file", metavar = "FILE")
options, args = parser.parse_args()

indir   = options.indir
outfile = options.outfile

vars     = zeros((0), dtype = '|S32')
counties = zeros((0))

files = listdir(indir)
for i in range(len(files)):
    with nc(indir + sep + files[i]) as f:
        vars     = unique(append(vars, f.variables['var'].long_name.split(', ')))
        counties = unique(append(counties, f.variables['county'][:]))

with nc(outfile, 'w') as f:
    f.createDimension('var', len(vars))
    vvar = f.createVariable('var', 'i4', 'var')
    vvar[:] = range(1, len(vars) + 1)
    vvar.units = 'mapping'
    vvar.long_name = ', '.join(vars)

    f.createDimension('county', len(counties))
    countyvar = f.createVariable('county', 'f8', 'county')
    countyvar[:] = counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'