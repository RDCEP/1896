#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import where, resize, setdiff1d, sqrt

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "Campaign.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-r", dest = "radius", default = 0.5, type = "float",
                  help = "Smoothing radius in degrees")
parser.add_option("--wlat", dest = "wlat", default = 1, type = "float",
                  help = "Weight assigned to latitude in distance metric (increasing weight leads to horizontal ellipse)")
parser.add_option("--wlon", dest = "wlon", default = 1, type = "float",
                  help = "Weight assigned to longitude in distance metric (increasing weight leads to vertical ellipse)")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "Campaign.smooth.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
radius     = options.radius
wlat       = options.wlat
wlon       = options.wlon
outputfile = options.outputfile

copyfile(inputfile, outputfile)

fi = nc(inputfile)

lats, lons = fi.variables['lat'][:], fi.variables['lon'][:]

latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

variables = setdiff1d(fi.variables.keys(), fi.dimensions.keys()) # exclude dimension variables

with nc(outputfile, 'a') as fo:
    for i in range(len(variables)):
        vi = fi.variables[variables[i]][:]
        vo = fo.variables[variables[i]][:]

        sh = vi.shape
        if len(sh) == 2:
            vmask = vi.mask
        elif len(sh) == 3:
            vmask = vi[0].mask
        elif len(sh) == 4:
            vmask = vi[0, 0].mask
        else:
            raise Exception('Unknown dimension size for variable %s' % variables[i])

        latidx, lonidx = where(~vmask)
        latdv,  londv  = latd[latidx, lonidx], lond[latidx, lonidx]

        for j in range(len(latidx)):
            lidx1, lidx2 = latidx[j], lonidx[j]

            inrange = sqrt(wlat * (latdv - lats[lidx1]) ** 2 + wlon * (londv - lons[lidx2]) ** 2) < radius

            if len(sh) == 2:
                vo[lidx1, lidx2] = vi[latidx[inrange], lonidx[inrange]].mean()
            elif len(sh) == 3:
                vo[:, lidx1, lidx2] = vi[:, latidx[inrange], lonidx[inrange]].mean(axis = 1)
            else:
                vo[:, :, lidx1, lidx2] = vi[:, :, latidx[inrange], lonidx[inrange]].mean(axis = 2)

        vvo = fo.variables[variables[i]] # replace with smoothed variable
        vvo[:] = vo

fi.close()