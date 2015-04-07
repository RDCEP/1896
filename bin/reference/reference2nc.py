#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import arange
from optparse import OptionParser
from netCDF4 import Dataset as nc
from Reference import ReferenceCombiner

# parse inputs
parser = OptionParser()
parser.add_option("-y", "--yieldfiles", dest = "yieldfiles", default = "maize.yield.csv,maize.yield_irr.csv", type = "string",
                  help = "Sum and irrigated yield files separated by comma")
parser.add_option("-a", "--hareafiles", dest = "hareafiles", default = "maize.harvested_area.csv,maize.harvested_area_irr.csv", type = "string",
                  help = "Sum and irrigated harvested area files separated by comma")
parser.add_option("-s", "--censusfile", dest = "censusfile", default = "maize.census_areas.csv", type = "string",
                  help = "Census file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

yieldfiles = options.yieldfiles
hareafiles = options.hareafiles
censusfile = options.censusfile
trange     = options.trange
cropname   = options.cropname
outputfile = options.outputfile

yieldfile, yieldirrfile = yieldfiles.split(',')
hareafile, hareairrfile = hareafiles.split(',')

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

# load reference data
ref        = ReferenceCombiner(yieldfile, yieldirrfile, hareafile, hareairrfile, censusfile, cropname)
counties   = ref.counties
irr        = ref.irr
cyld, chvt = ref.getVar(years)

with nc(outputfile, 'w') as f:
    f.createDimension('time', len(years))
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = years - years[0]
    yearsvar.units = 'years since %d' % years[0]
    yearsvar.long_name = 'time'

    f.createDimension('county', len(counties))
    countyvar = f.createVariable('county', 'i4', 'county')
    countyvar[:] = counties
    countyvar.units = ''
    countyvar.long_name = 'county number'

    f.createDimension('irr', len(irr))
    irrvar = f.createVariable('irr', 'i4', 'irr')
    irrvar[:] = range(1, 1 + len(irr))
    irrvar.units = 'mapping'
    irrvar.long_name = ', '.join(irr)

    yvar = f.createVariable('yield', 'f4', ('time', 'county', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yvar[:] = cyld
    yvar.units = 'kg/ha'
    yvar.long_name = 'harvested yield'

    avar = f.createVariable('area', 'f4', ('time', 'county', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = chvt
    avar.units = 'ha'
    avar.long_name = 'harvested area'