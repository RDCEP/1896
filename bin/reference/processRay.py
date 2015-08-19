#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import zeros, ones, isnan
from numpy.ma import masked_array, masked_where

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "ray.mai.1961-2008.nc4", type = "string",
                  help = "Input netcdf file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.yield.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
outputfile = options.outputfile

with nc(inputfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    time     = f.variables['time'][:]
    tunits   = f.variables['time'].units
    yld      = f.variables['yield'][:]
    area     = f.variables['area'][:]

yld  = 1000. * masked_where(isnan(yld), yld) # convert to kg/ha
area = masked_where(isnan(area), area)

ntimes, nlats, nlons, nirr = len(time), len(lat), len(lon), 3

yld2  = masked_array(zeros((ntimes, nlats, nlons, nirr)), mask = ones((ntimes, nlats, nlons, nirr)))
area2 = masked_array(zeros((ntimes, nlats, nlons, nirr)), mask = ones((ntimes, nlats, nlons, nirr)))

for i in range(nirr):
    yld2[:, :, :, i]  = yld
    area2[:, :, :, i] = area

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time
    yearsvar.units = tunits
    yearsvar.long_name = 'time'

    f.createDimension('lat', nlats)
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lat
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', nlons)
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lon
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    f.createDimension('irr', nirr)
    irrvar = f.createVariable('irr', 'i4', 'irr')
    irrvar[:] = range(1, 4)
    irrvar.units = 'mapping'
    irrvar.long_name = 'ir, rf, sum'

    yldvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yldvar[:] = yld2
    yldvar.units = 'kg/ha'
    yldvar.long_name = 'harvested yield'

    areavar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    areavar[:] = area2
    areavar.units = 'ha'
    areavar.long_name = 'harvested area'