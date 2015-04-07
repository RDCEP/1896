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

yrs = [2014]
day_start = [96]

nyrs = len(yrs)
nweeks = 35

with nc(infile) as f:
    days     = f.variables['day'][:]
    vars     = f.variables['var'].long_name.split(', ')
    counties = f.variables['county'][:]

    data = f.variables['data'][:]

sh = (nyrs, nweeks, len(vars), len(counties))

data2 = masked_array(zeros(sh), mask = ones(sh))

daymat = zeros((nyrs, nweeks))

for i in range(nyrs):
    ds = day_start[i]
    for j in range(nweeks):
        daymat[i, j] = ds + j * 7
        day = yrs[i] * 1000 + daymat[i, j]
        if day in days:
            dayidx = where(days == day)[0][0]
            data2[i, j] = data[dayidx]

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
    vvar[:] = range(1, 1 + len(vars))
    vvar.long_name = ', '.join(vars)

    f.createDimension('county', len(counties))
    countyvar = f.createVariable('county', 'f8', 'county')
    countyvar[:] = counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'

    dayvar = f.createVariable('day', 'i4', ('year', 'week'))
    dayvar[:] = daymat
    dayvar.units = 'julian day'
    dayvar.long_name = 'day'

    datavar = f.createVariable('data', 'f4', ('year', 'week', 'var', 'county'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    datavar[:] = data2