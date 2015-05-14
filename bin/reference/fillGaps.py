#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import where
from optparse import OptionParser
from netCDF4 import Dataset as nc

def fill(var, mask, lat, lon):
    var2 = var.copy()

    badgrid = var2.mask.all(axis = 2)

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
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.reference.nc4", type = "string",
                  help = "Input netcdf file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.reference.filled.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
outputfile = options.outputfile

with nc(inputfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    time     = f.variables['time'][:]
    irr      = f.variables['irr'][:]

    tunits = f.variables['time'].units

    yld = f.variables['yield'][:]
    area = f.variables['area'][:]
    marea = f.variables['area_mirca'][:]

with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

for i in range(len(time)):
    yld[i] = fill(yld[i], mask, lat, lon)
    area[i] = fill(area[i], mask, lat, lon)
    marea[i] = fill(marea[i], mask, lat, lon)

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

    f.createDimension('irr', len(irr))
    irrvar = f.createVariable('irr', 'i4', 'irr')
    irrvar[:] = irr
    irrvar.units = 'ir, rf, sum'
    irrvar.long_name = 'mapping'

    yldvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yldvar[:] = yld
    yldvar.units = 'kg/ha'
    yldvar.long_name = 'harvested yield'

    areavar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    areavar[:] = area
    areavar.units = 'ha'
    areavar.long_name = 'harvested area'

    mareavar = f.createVariable('area_mirca', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mareavar[:] = marea
    mareavar.units = 'ha'
    mareavar.long_name = 'harvested area'