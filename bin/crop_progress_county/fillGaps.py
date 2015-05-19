#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import where, setdiff1d

def fill(var, lat, lon):
    var2 = var.copy()

    badgrid = var2.mask.any(axis = 2)

    glatidx, glonidx = where(~badgrid)
    glat,    glon    = lat[glatidx], lon[glonidx]

    if not glat.size: # no good points
        return var2

    badgrid[mask.mask] = False
    latidx, lonidx = where(badgrid)

    for i in range(len(latidx)):
        midx = ((glat - lat[latidx[i]]) ** 2 + (glon - lon[lonidx[i]]) ** 2).argmin()

        var2[latidx[i], lonidx[i]] = var[glatidx[midx], glonidx[midx]]

    return var2

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.crop_progress.2009-2014.nc4", type = "string",
                  help = "Input netcdf file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.2009-2014.filled.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
outputfile = options.outputfile

with nc(inputfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    time     = f.variables['time'][:]
    per      = f.variables['per'][:]

    tunits = f.variables['time'].units

    vars = setdiff1d(f.variables.keys(), ['time', 'lat', 'lon', 'per'])

    varr       = [0] * len(vars)
    vunits     = [0] * len(vars)
    vlongnames = [0] * len(vars)
    for i in range(len(vars)):
        varr[i]       = f.variables[vars[i]][:]
        vunits[i]     = f.variables[vars[i]].units
        vlongnames[i] = f.variables[vars[i]].long_name

with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

for i in range(len(vars)):
    v = varr[i]
    for j in range(len(time)):
        v[j] = fill(v[j], lat, lon)
    varr[i] = v

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time
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

    f.createDimension('per', len(per))
    pervar = f.createVariable('per', 'i4', 'per')
    pervar[:] = per
    pervar.units = '%'
    pervar.long_name = 'percentage'

    for i in range(len(vars)):
        vvar = f.createVariable(vars[i], 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
        vvar[:] = varr[i]
        vvar.units = vunits[i]
        vvar.long_name = vlongnames[i]