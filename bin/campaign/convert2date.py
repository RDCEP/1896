#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from numpy import where
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from datetime import datetime, timedelta

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "p0.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-v", "--variable", dest = "variable", default = "p0", type = "string",
                  help = "Variable to process")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "p0.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
variable   = options.variable
outputfile = options.outputfile

with nc(inputfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    timeorig = f.variables['time'][:].astype(int)
    tunits   = f.variables['time'].units
    var      = f.variables[variable][:]  # var(time, lat, lon)

time = timeorig + int(findall(r'\d+', tunits)[0])
if 'growing' in tunits: time -= 1 # time in growing seasons
dtimes = [datetime(time[t], 1, 1) for t in range(len(time))]

latidx, lonidx = where(~var[0].mask)

# convert to YYYYMMDD
var2 = var.copy().astype(int)
var2.fill_value = 999999
for i in range(len(latidx)):
    jday = var[:, latidx[i], lonidx[i]]
    var2[:, latidx[i], lonidx[i]] = [int((dtimes[j] + timedelta(int(jday[j] - 1))).strftime('%Y%m%d')) for j in range(len(dtimes))]

copyfile(inputfile, outputfile)

with nc(outputfile, 'w') as f:
    f.createDimension('time', len(time))
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = timeorig
    yearsvar.units = tunits
    yearsvar.long_name = 'time'

    f.createDimension('lat', len(lat))
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lat
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', len(lon))
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lon
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    vvar = f.createVariable(variable, 'i4', ('time', 'lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 999999)
    vvar[:] = var2
    vvar.units = 'YYYYMMDD'
    vvar.long_name = variable