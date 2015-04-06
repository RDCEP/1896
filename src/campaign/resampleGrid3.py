#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, isMaskedArray
from numpy import zeros, ones, arange, where, resize, logical_not, newaxis

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "plpop.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "mask.all.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-v", "--variable", dest = "variable", default = "plpop", type = "string",
                  help = "Variable name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "plpop.resamp.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
trange     = options.trange
variable   = options.variable
outputfile = options.outputfile

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    time       = f.variables['time'][:]
    tunits     = f.variables['time'].units
    ir         = f.variables['ir'].long_name.split(',')
    var        = f.variables[variable][:] # var(ir, time, lat, lon)
    vunits     = f.variables[variable].units
    vlongname  = f.variables[variable].long_name

time += int(findall(r'\d+', tunits)[0]) - 1

tidx1, tidx2 = where(years == time[0])[0][0], where(years == time[-1])[0][0]

if isMaskedArray(var):
    vmask = var[0, 0].mask # variable mask
else:
    vmask = zeros((len(lats), len(lons)))

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

# convert to 1D arrays
latd = latd[logical_not(vmask)]
lond = lond[logical_not(vmask)]

latidx, lonidx = where(logical_not(vmask))
var = var[:, :, latidx, lonidx]

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale to grid level
nyears, nlats, nlons, nir = len(years), len(mlats), len(mlons), len(ir)
var2 = masked_array(zeros((nir, nyears, nlats, nlons)), mask = ones((nir, nyears, nlats, nlons)))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    totd = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    midx = totd.argmin()

    var2[:, tidx1 : tidx2 + 1, l1, l2] = var[:, :, midx]

    # extrapolate
    var2[:, : tidx1,     l1, l2] = var[:, 0,  midx, newaxis]
    var2[:, tidx2 + 1 :, l1, l2] = var[:, -1, midx, newaxis]

with nc(outputfile, 'w') as f:
    f.createDimension('time', nyears)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = years - years[0]
    yearsvar.units = 'years since %d' % years[0]
    yearsvar.long_name = 'time'

    f.createDimension('ir', nir)
    irrvar = f.createVariable('ir', 'i4', 'ir')
    irrvar[:] = range(1, 1 + nir)
    irrvar.units = 'mapping'
    irrvar.long_name = ', '.join(ir)

    f.createDimension('lat', nlats)
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = mlats
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', nlons)
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = mlons
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    vvar = f.createVariable(variable, 'f4', ('ir', 'time', 'lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    vvar[:] = var2
    vvar.units = vunits
    vvar.long_name = vlongname