#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array
from numpy import zeros, ones, where, resize, setdiff1d, sqrt, array, logical_or

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
parser.add_option("-d", dest = "dthres", default = 0.5, type = "float",
                  help = "Degree threshold beyond which to average over nearest latitude bands")
parser.add_option("-n", dest = "nbands", default = 5, type = "int",
                  help = "Number of nearest latitude bands over which to average")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "Campaign.extrap.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
wlat       = options.wlat
wlon       = options.wlon
dthres     = options.dthres
nbands     = options.nbands
outputfile = options.outputfile

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]

    variables = setdiff1d(f.variables.keys(), f.dimensions.keys()) # exclude dimension variables
    varnames  = []
    varrs     = []
    shapes    = []
    vmasks    = []
    for i in range(len(variables)):
        v = f.variables[variables[i]]

        if 'lat' in v.dimensions and 'lon' in v.dimensions:
            varnames.append(variables[i])

            varr = v[:]

            sh = v.shape
            if len(sh) == 2:
                vmask          = varr.mask
                latidx, lonidx = where(~vmask)
                varr           = varr[latidx, lonidx]
            elif len(sh) == 3:
                vmask          = varr[0].mask
                latidx, lonidx = where(~vmask)
                varr           = varr[:, latidx, lonidx]
            elif len(sh) == 4:
                vmask          = varr[0, 0].mask
                latidx, lonidx = where(~vmask)
                varr           = varr[:, :, latidx, lonidx]
            else:
                raise Exception('Unknown dimension size for variable %s' % variables[i])

            varrs.append(varr)
            vmasks.append(vmask)
            shapes.append(sh)

nvars = len(varnames)

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(~mask.mask)

# extrapolate
varr2 = [0] * nvars
for i in range(nvars):
    sh = shapes[i]

    varr2[i] = masked_array(zeros(sh), mask = ones(sh))

    # convert to 1D arrays
    lat1d, lon1d = latd[~vmasks[i]], lond[~vmasks[i]]

    # indicates whether data is in latitude band
    dlat = ~vmasks[i].all(axis = 1)

    for j in range(len(latidx)):
        l1, l2 = latidx[j], lonidx[j]

        totd = sqrt(wlat * (lat1d - mlats[l1]) ** 2 + wlon * (lon1d - mlons[l2]) ** 2)
        mind = totd.min()

        if mind < dthres:
            midx = totd.argmin()

            if len(sh) == 2:
                varr2[i][l1, l2] = varrs[i][midx]
            elif len(sh) == 3:
                varr2[i][:, l1, l2] = varrs[i][:, midx]
            else:
                varr2[i][:, :, l1, l2] = varrs[i][:, :, midx]
        else:
            # average closest latitude bands
            totd    = (lats - mlats[l1]) ** 2
            sortidx = array([idx[0] for idx in sorted(enumerate(totd), key = lambda x: x[1])])
            sortidx = sortidx[dlat[sortidx]]
            sortidx = sortidx[: nbands] # select first nbands

            inlat = zeros(len(lat1d))
            for k in range(len(sortidx)):
                inlat = logical_or(inlat, lat1d == lats[sortidx[k]])

            if len(sh) == 2:
                varr2[i][l1, l2] = varrs[i][inlat].mean()
            elif len(sh) == 3:
                varr2[i][:, l1, l2] = varrs[i][:, inlat].mean(axis = 1)
            else:
                varr2[i][:, :, l1, l2] = varrs[i][:, :, inlat].mean(axis = 2)

copyfile(inputfile, outputfile)

with nc(outputfile, 'a') as f:
    for i in range(nvars):
        vvar = f.variables[varnames[i]]
        vvar[:] = varr2[i]