#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, isMaskedArray
from numpy import zeros, ones, where, resize, setdiff1d, sqrt, double

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "Campaign.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "mask.all.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("--wlat", dest = "wlat", default = 1, type = "float",
                  help = "Weight assigned to latitude in distance metric (increasing weight leads to horizontal ellipse)")
parser.add_option("--wlon", dest = "wlon", default = 1, type = "float",
                  help = "Weight assigned to longitude in distance metric (increasing weight leads to vertical ellipse)")
parser.add_option("-r", dest = "radii", default = "0.5", type = "string",
                  help = "Comma-separated list of smoothing radii in degrees")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "Campaign.extrap.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
wlat       = options.wlat
wlon       = options.wlon
radii      = options.radii
outputfile = options.outputfile

radii = [double(r) for r in radii.split(',')]

copyfile(inputfile, outputfile)

fi = nc(inputfile)

lats, lons = fi.variables['lat'][:], fi.variables['lon'][:]

latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

variables = setdiff1d(fi.variables.keys(), fi.dimensions.keys()) # exclude dimension variables

with nc(maskfile) as f:
    mask = f.variables['mask'][:]

latidx, lonidx = where(~mask.mask) # find unmasked points

with nc(outputfile, 'a') as fo:
    for i in range(len(variables)):
        dims = fi.variables[variables[i]].dimensions
        if not 'lat' in dims or not 'lon' in dims:
            continue

        ntimes = fi.variables['time'].size if 'time' in dims else 1

        vi = fi.variables[variables[i]][:]
        vo = masked_array(zeros(vi.shape), mask = ones(vi.shape))

        sh = vi.shape

        for j in range(ntimes):
            if len(sh) == 2:
                vmask = vi.mask
            elif len(sh) == 3:
                vmask = vi[j].mask
            elif len(sh) == 4:
                vmask = vi[j, 0].mask
            else:
                raise Exception('Unknown dimension size for variable %s' % variables[i])

            latidxv, lonidxv = where(~vmask)
            latdv,   londv   = latd[latidxv, lonidxv], lond[latidxv, lonidxv]

            for k in range(len(latidx)):
                lidx1, lidx2 = latidx[k], lonidx[k]

                if vmask[lidx1, lidx2]:
                    for m in range(len(radii)):
                        inrange = sqrt(wlat * (latdv - lats[lidx1]) ** 2 + wlon * (londv - lons[lidx2]) ** 2) < radii[m]

                        if len(sh) == 2:
                            smoothed = vi[latidxv[inrange], lonidxv[inrange]].mean()
                            vo[lidx1, lidx2] = smoothed
                        elif len(sh) == 3:
                            smoothed = vi[j, latidxv[inrange], lonidxv[inrange]].mean()
                            vo[j, lidx1, lidx2] = smoothed
                        else:
                            smoothed = vi[j, :, latidxv[inrange], lonidxv[inrange]].mean(axis = 0)
                            vo[j, :, lidx1, lidx2] = smoothed

                        if not isMaskedArray(smoothed) or not smoothed.mask.all():
                            break
                else:
                    if len(sh) == 2:
                        vo[lidx1, lidx2] = vi[lidx1, lidx2]
                    elif len(sh) == 3:
                        vo[j, lidx1, lidx2] = vi[j, lidx1, lidx2]
                    else:
                        vo[j, :, lidx1, lidx2] = vi[j, :, lidx1, lidx2]

        vvo = fo.variables[variables[i]] # replace with smoothed extrapolated variable
        vvo[:] = vo

fi.close()