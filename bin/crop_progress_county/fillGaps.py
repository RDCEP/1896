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

    cplanting = f.variables['planting'][:]
    canthesis = f.variables['anthesis'][:]
    cmaturity = f.variables['maturity'][:]

    splanting = f.variables['planting_state'][:]
    santhesis = f.variables['anthesis_state'][:]
    smaturity = f.variables['maturity_state'][:]

with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

for i in range(len(time)):
    cplanting[i] = fill(cplanting[i], lat, lon)
    canthesis[i] = fill(canthesis[i], lat, lon)
    cmaturity[i] = fill(cmaturity[i], lat, lon)

    splanting[i] = fill(splanting[i], lat, lon)
    santhesis[i] = fill(santhesis[i], lat, lon)
    smaturity[i] = fill(smaturity[i], lat, lon)

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

    cpvar = f.createVariable('planting', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    cpvar[:] = cplanting
    cpvar.units = 'julian day'
    cpvar.long_name = 'planting'

    cavar = f.createVariable('anthesis', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    cavar[:] = canthesis
    cavar.units = 'julian day'
    cavar.long_name = 'anthesis'

    cmvar = f.createVariable('maturity', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    cmvar[:] = cmaturity
    cmvar.units = 'julian day'
    cmvar.long_name = 'maturity'

    spvar = f.createVariable('planting_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    spvar[:] = splanting
    spvar.units = 'julian day'
    spvar.long_name = 'planting'

    savar = f.createVariable('anthesis_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    savar[:] = santhesis
    savar.units = 'julian day'
    savar.long_name = 'anthesis'

    smvar = f.createVariable('maturity_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    smvar[:] = smaturity
    smvar.units = 'julian day'
    smvar.long_name = 'maturity'