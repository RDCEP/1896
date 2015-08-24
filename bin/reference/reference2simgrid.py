#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from numpy.ma import masked_array
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import resize, cos, pi, ones, zeros, double, where

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.reference.nc4", type = "string",
                  help = "Input reference netcdf4 file", metavar = "FILE")
parser.add_option("-p", "--per", dest = "per", default = "1", type = "string",
                  help = "Percent threshold")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.mask.0.01.nc4", type = "string",
                  help = "Output sim grid netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
per        = options.per
outputfile = options.outputfile

per = double(per)

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    time       = f.variables['time'][:]
    tunits     = f.variables['time'].units
    rarea      = f.variables['area'][:, :, :, 2] # sum area

# average area from 1998-2007
time += int(findall(r'\d+', tunits)[0])
tidx0, tidx1 = where(time == 1998)[0][0], where(time == 2007)[0][0] + 1
rarea = rarea[tidx0 : tidx1].mean(axis = 0)

lat_delta = abs(lats[0] - lats[1])
nlats, nlons = len(lats), len(lons)

area = 100 * (lat_delta * 111.2) ** 2 * cos(pi * lats / 180)
area = per / 100. * resize(area, (nlons, nlats)).T

mask = masked_array(zeros((nlats, nlons)), mask = ones((nlats, nlons)))
mask[rarea > area] = 1

with nc(outputfile, 'w'):
    f.createDimension('lat', nlats)
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lats
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', nlons)
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lons
    lonvar.units = 'degrees_east'

    mvar = f.createVariable('mask', 'f4', ('lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = mask