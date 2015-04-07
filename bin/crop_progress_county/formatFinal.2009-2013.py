#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from numpy.ma import masked_array
from netCDF4 import Dataset as nc
from numpy import ones, zeros, where

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--infile", dest = "infile", default = "", type = "string",
                  help = "Input file", metavar = "FILE")
parser.add_option("-o", "--outfile", dest = "outfile", default = "", type = "string",
                  help = "Output file", metavar = "FILE")
options, args = parser.parse_args()

infile  = options.infile
outfile = options.outfile

yrs = [2009, 2010, 2011, 2012, 2013]
day_start = [95, 94, 93, 92, 90]

nyrs   = len(yrs)
nweeks = 35

with nc(infile) as f:
    days     = f.variables['day'][:]
    vars     = f.variables['var'][:]
    counties = f.variables['county'][:]

    ndata  = f.variables['ndata'][:]
    nadata = f.variables['nadata'][:]

sh = (nyrs, nweeks, len(vars), len(counties))

ndata2  = masked_array(zeros(sh), mask = ones(sh))
nadata2 = masked_array(zeros(sh), mask = ones(sh))

daymat = zeros((nyrs, nweeks))

for i in range(nyrs):
    ds = day_start[i]
    for j in range(nweeks):
        daymat[i, j] = ds + j * 7
        day = yrs[i] * 1000 + daymat[i, j]
        if day in days:
            dayidx = where(days == day)[0][0]
            ndata2[i, j] = ndata[dayidx]
            nadata2[i, j] = nadata[dayidx]

with nc(outfile, 'w') as f:
    f.createDimension('year', None)
    yearvar = f.createVariable('year', 'i4', 'year')
    yearvar[:] = yrs
    yearvar.long_name = 'year'

    f.createDimension('week', nweeks)
    weekvar = f.createVariable('week', 'i4', 'week')
    weekvar[:] = range(1, 1 + nweeks)
    weekvar.long_name = 'week'

    f.createDimension('var', len(vars))
    vvar = f.createVariable('var', 'i4', 'var')
    vvar[:] = vars
    vvar.long_name = 'variable'

    f.createDimension('county', len(counties))
    countyvar = f.createVariable('county', 'f8', 'county')
    countyvar[:] = counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'

    dayvar = f.createVariable('day', 'i4', ('year', 'week'))
    dayvar[:] = daymat
    dayvar.units = 'julian day'
    dayvar.long_name = 'day'

    ndatavar = f.createVariable('ndata', 'f4', ('year', 'week', 'var', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    ndatavar[:] = ndata2

    nadatavar = f.createVariable('nadata', 'f4', ('year', 'week', 'var', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    nadatavar[:] = nadata2