#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array
from numpy import zeros, ones, where, resize, logical_not

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "Campaign.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "mask.all.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-v", "--variable", dest = "variable", default = "cult_p1", type = "string",
                  help = "Variable name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "Campaign.extrap.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
variable   = options.variable
outputfile = options.outputfile

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    var        = f.variables[variable][:]

# variable mask
sh = var.shape
if len(sh) == 2:
    vmask = var.mask
elif len(sh) == 3:
    vmask = var[0].mask
elif len(sh) == 4:
    vmask = var[0, 0].mask
else:
    raise Exception('Unknown dimension size')

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

# convert to 1D arrays
latd = latd[~vmask]
lond = lond[~vmask]

latidx, lonidx = where(logical_not(vmask))
if len(sh) == 2:
    var = var[latidx, lonidx]
elif len(sh) == 3:
    var = var[:, latidx, lonidx]
else:
    var = var[:, :, latidx, lonidx]

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# extrapolate
var2 = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    totd = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    midx = totd.argmin()

    if len(sh) == 2:
        var2[l1, l2] = var[midx]
    elif len(sh) == 3:
        var2[:, l1, l2] = var[:, midx]
    else:
        var2[:, :, l1, l2] = var[:, :, midx]

copyfile(inputfile, outputfile)

with nc(outputfile, 'a') as f:
    vvar = f.variables[variable]
    vvar[:] = var2