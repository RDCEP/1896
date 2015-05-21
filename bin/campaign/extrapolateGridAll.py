#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array
from numpy import zeros, ones, where, resize, setdiff1d

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "Campaign.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "mask.all.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("--wlat", dest = "wlat", default = 1, type = "float",
                  help = "Weight assigned to latitude in distance metric")
parser.add_option("--wlon", dest = "wlon", default = 1, type = "float",
                  help = "Weight assigned to longitude in distance metric")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "Campaign.extrap.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
wlat       = options.wlat
wlon       = options.wlon
outputfile = options.outputfile

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]

    variables = setdiff1d(f.variables.keys(), f.dimensions.keys()) # exclude dimension variables
    varnames  = []
    varr      = []
    shapes    = []
    for i in range(len(variables)):
        v = f.variables[variables[i]]
        if 'lat' in v.dimensions and 'lon' in v.dimensions:
            varnames.append(variables[i])
            varr.append(v[:])
            shapes.append(v.shape)

nvars = len(varnames)

# variable mask (assume it's the same across variables)
sh = shapes[0]
if len(sh) == 2:
    vmask = varr[0].mask
elif len(sh) == 3:
    vmask = varr[0][0].mask
elif len(sh) == 4:
    vmask = varr[0][0, 0].mask
else:
    raise Exception('Unknown dimension size')

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

# convert to 1D arrays
latd = latd[~vmask]
lond = lond[~vmask]

latidx, lonidx = where(~vmask)
for i in range(nvars):
    sh = shapes[i]
    if len(sh) == 2:
        varr[i] = varr[i][latidx, lonidx]
    elif len(sh) == 3:
        varr[i] = varr[i][:, latidx, lonidx]
    else:
        varr[i] = varr[i][:, :, latidx, lonidx]

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(~mask.mask)

# extrapolate
varr2 = [0] * nvars
for i in range(nvars):
    varr2[i] = masked_array(zeros(shapes[i]), mask = ones(shapes[i]))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    totd = wlat * (latd - mlats[l1]) ** 2 + wlon * (lond - mlons[l2]) ** 2
    midx = totd.argmin()

    for j in range(nvars):
        sh = shapes[j]
        if len(sh) == 2:
            varr2[j][l1, l2] = varr[j][midx]
        elif len(sh) == 3:
            varr2[j][:, l1, l2] = varr[j][:, midx]
        else:
            varr2[j][:, :, l1, l2] = varr[j][:, :, midx]

copyfile(inputfile, outputfile)

with nc(outputfile, 'a') as f:
    for i in range(nvars):
        vvar = f.variables[varnames[i]]
        vvar[:] = varr2[i]