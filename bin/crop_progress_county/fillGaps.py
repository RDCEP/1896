#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import where
from optparse import OptionParser
from netCDF4 import Dataset as nc

def fill(var, lat, lon):
    var2 = var.copy()

    badgrid = var2.mask.any(axis = 2)

    glatidx, glonidx = where(~badgrid)
    glat,    glon    = lat[glatidx], lon[glonidx]

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

    planting = f.variables['planting'][:]
    anthesis = f.variables['anthesis'][:]
    maturity = f.variables['maturity'][:]

with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

for i in range(len(time)):
    p = fill(planting[i], lat, lon)
    a = fill(anthesis[i], lat, lon)
    m = fill(maturity[i], lat, lon)

    planting[i] = p
    anthesis[i] = a
    maturity[i] = m

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

    pvar = f.createVariable('planting', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    pvar[:] = planting
    pvar.units = 'julian day'
    pvar.long_name = 'planting'

    avar = f.createVariable('anthesis', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = anthesis
    avar.units = 'julian day'
    avar.long_name = 'anthesis'

    mvar = f.createVariable('maturity', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = maturity
    mvar.units = 'julian day'
    mvar.long_name = 'maturity'

    with nc(inputfile) as fi: # copy state data
        psvar = f.createVariable('planting_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
        psvar[:] = fi.variables['planting_state'][:]
        psvar.units = 'julian day'
        psvar.long_name = 'planting'

        asvar = f.createVariable('anthesis_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
        asvar[:] = fi.variables['anthesis_state'][:]
        asvar.units = 'julian day'
        asvar.long_name = 'anthesis'

        msvar = f.createVariable('maturity_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
        msvar[:] = fi.variables['maturity_state'][:]
        msvar.units = 'julian day'
        msvar.long_name = 'maturity'