#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, isMaskedArray
from numpy import zeros, ones, where, resize, logical_not, logical_and, isnan

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.napprate.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "mask.all.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-v", "--variable", dest = "variable", default = "maize_napprate", type = "string",
                  help = "Variable name")
parser.add_option("--wlat", dest = "wlat", default = 1, type = "float",
                  help = "Weight assigned to latitude in distance metric")
parser.add_option("--wlon", dest = "wlon", default = 1, type = "float",
                  help = "Weight assigned to longitude in distance metric")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.napprate.resamp.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
variable   = options.variable
wlat       = options.wlat
wlon       = options.wlon
outputfile = options.outputfile

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    var        = f.variables[variable][:] # var(lat, lon)
    vunits     = f.variables[variable].units
    vlongname  = f.variables[variable].long_name

latinrange = logical_and(lats >= 24,   lats <= 56) # limit range
loninrange = logical_and(lons >= -130, lons <= -60)
lats, lons = lats[latinrange], lons[loninrange]
var = var[latinrange][:, loninrange]

if isMaskedArray(var):
    vmask = var.mask
else:
    vmask = zeros(var.shape, dtype = bool) # no mask
vmask = logical_and(~isnan(var), ~vmask) # remove NaNs

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

# convert to 1D arrays
latd = latd[vmask]
lond = lond[vmask]
var  = var[vmask]

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale to grid level
nlats, nlons = len(mlats), len(mlons)
var2 = masked_array(zeros((nlats, nlons)), mask = ones((nlats, nlons)))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    totd = wlat * (latd - mlats[l1]) ** 2 + wlon * (lond - mlons[l2]) ** 2
    midx = totd.argmin()

    var2[l1, l2] = var[midx]

    # if mlats[l1] > 50 and mlats[l1] <= 52:
    #     var2[l1, l2] = 990028
    # elif mlats[l1] > 52 and mlats[l1] <= 54:
    #     var2[l1, l2] = 990014
    # elif mlats[l1] > 54 and mlats[l1] <= 56:
    #     var2[l1, l2] = 990001

with nc(outputfile, 'w') as f:
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

    vvar = f.createVariable(variable, 'f4', ('lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    vvar[:] = var2
    vvar.units = vunits
    vvar.long_name = vlongname