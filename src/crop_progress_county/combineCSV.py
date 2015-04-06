#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from fnmatch import filter
from os import listdir, sep
from optparse import OptionParser
from numpy.ma import masked_array
from netCDF4 import Dataset as nc
from numpy import ones, zeros, where

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--indir", dest = "indir", default = "", type = "string",
                  help = "Input directory")
parser.add_option("-d", "--date", dest = "date", default = "", type = "string",
                  help = "Date in YYYYMMDD")
parser.add_option("-f", "--dimfile", dest = "dimfile", default = "", type = "string",
                  help = "Netcdf file of var and county dimensions", metavar = "FILE")
parser.add_option("-o", "--outdir", dest = "outdir", default = "", type = "string",
                  help = "Output directory")
options, args = parser.parse_args()

indir   = options.indir
date    = options.date
dimfile = options.dimfile
outdir  = options.outdir

with nc(dimfile) as f:
    vars     = f.variables['var'].long_name.split(', ')
    counties = f.variables['county'][:]

nvars, ncounties = len(vars), len(counties)

files = filter(listdir(indir), '*' + date + '*')

with nc(indir + sep + files[0]) as f:
    day = f.variables['day'][:]

fulldata = masked_array(zeros((1, nvars, ncounties)), mask = ones((1, nvars, ncounties)))

for i in range(len(files)):
    with nc(indir + sep + files[i]) as f:
        var    = f.variables['var'].long_name.split(', ')
        county = f.variables['county'][:]
        data   = f.variables['data'][:]

        for j in range(len(var)):
            vidx = vars.index(var[j])
            for k in range(len(county)):
                cidx = where(counties == county[k])[0][0]
                fulldata[0, vidx, cidx] = data[j, 0, k]

with nc(outdir + sep + 'out_' + date + '.nc4', 'w') as f:
    f.createDimension('day', None)
    dayvar = f.createVariable('day', 'i4', 'day')
    dayvar[:] = day
    dayvar.units = 'YYYYDDD'
    dayvar.long_name = 'time'

    f.createDimension('var', nvars)
    vvar = f.createVariable('var', 'i4', 'var')
    vvar[:] = range(1, nvars + 1)
    vvar.units = 'mapping'
    vvar.long_name = ', '.join(vars)

    f.createDimension('county', ncounties)
    countyvar = f.createVariable('county', 'f8', 'county')
    countyvar[:] = counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'

    datavar = f.createVariable('data', 'f4', ('day', 'var', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    datavar[:] = fulldata