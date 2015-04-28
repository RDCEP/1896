#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import where
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import isMaskedArray

# parse inputs
parser = OptionParser()
parser.add_option("-c", "--cottonfile", dest = "cottonfile", default = "cotton-upland.reference.county.nc4", type = "string",
                  help = "County-level cotton-upland reference file", metavar = "FILE")
parser.add_option("-p", "--pimafile", dest = "pimafile", default = "cotton-pima.reference.county.nc4", type = "string",
                  help = "County-level cotton-pima reference file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "cotton.reference.county.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

cottonfile = options.cottonfile
pimafile   = options.pimafile
outputfile = options.outputfile

with nc(cottonfile) as f:
    time      = f.variables['time'][:]
    tunits    = f.variables['time'].units
    irr       = f.variables['irr'].long_name.split(', ')
    counties1 = f.variables['county'][:]
    yld1      = f.variables['yield'][:]
    area1     = f.variables['area'][:]

with nc(pimafile) as f:
    counties2 = f.variables['county'][:]
    yld2      = f.variables['yield'][:]
    area2     = f.variables['area'][:]

yld  = yld1.copy()
area = area1.copy()
for i in range(len(counties2)):
    cidx = where(counties1 == counties2[i])[0][0]
    for j in range(len(time)):
        for k in range(len(irr)):
            A1, Y1 = area1[j, cidx, k], yld1[j, cidx, k]
            A2, Y2 = area2[j, i, k],    yld2[j, i, k]

            if isMaskedArray(A1): A1 = 0
            if isMaskedArray(A2): A2 = 0
            if isMaskedArray(Y1): Y1 = 0
            if isMaskedArray(Y2): Y2 = 0

            if A1 + A2:
                yld[j, cidx, k] = (A1 * Y1 + A2 * Y2) / (A1 + A2)
            else:
                yld[j, cidx, k] = 0

with nc(outputfile, 'w') as f:
    f.createDimension('time', len(time))
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time
    yearsvar.units = tunits
    yearsvar.long_name = 'time'

    f.createDimension('county', len(counties1))
    countyvar = f.createVariable('county', 'i4', 'county')
    countyvar[:] = counties1
    countyvar.units = ''
    countyvar.long_name = 'county number'

    f.createDimension('irr', len(irr))
    irrvar = f.createVariable('irr', 'i4', 'irr')
    irrvar[:] = range(1, 1 + len(irr))
    irrvar.units = 'mapping'
    irrvar.long_name = ', '.join(irr)

    yvar = f.createVariable('yield', 'f4', ('time', 'county', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yvar[:] = yld
    yvar.units = 'kg/ha'
    yvar.long_name = 'harvested yield'

    avar = f.createVariable('area', 'f4', ('time', 'county', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = area
    avar.units = 'ha'
    avar.long_name = 'harvested area'