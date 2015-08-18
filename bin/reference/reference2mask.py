#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import unique
from numpy.ma import masked_where
from optparse import OptionParser
from netCDF4 import Dataset as nc

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.reference.county.nc4", type = "string",
                  help = "County-level reference netcdf4 file", metavar = "FILE")
parser.add_option("-f", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.mask.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
cmapfile   = options.cmapfile
outputfile = options.outputfile

with nc(inputfile) as f:
    counties = f.variables['county'][:]

with nc(cmapfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    cmap = f.variables['county'][:]

ucounties = unique(cmap)
ucounties = ucounties[~ucounties.mask]
for i in range(len(ucounties)):
    if not ucounties[i] in counties:
        cmap = masked_where(cmap == ucounties[i], cmap)

cmap[~cmap.mask] = 1

with nc(outputfile, 'w'):
    f.createDimension('lat', len(lat))
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lat
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', len(lon))
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lon
    lonvar.units = 'degrees_east'

    mvar = f.createVariable('mask', 'f4', ('lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = cmap