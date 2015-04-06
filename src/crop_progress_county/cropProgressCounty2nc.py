#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from CropProgressCountyAdapter import CropProgressCountyAdapter

# parse inputs
parser = OptionParser()
parser.add_option("--inputfile1", dest = "inputfile1", default = "out_2009-2013.final.nc4", type = "string",
                  help = "Input netcdf file for 2009-2013", metavar = "FILE")
parser.add_option("--inputfile2", dest = "inputfile2", default = "out_2014.final.nc4", type = "string",
                  help = "Input netcdf file for 2014", metavar = "FILE")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.2009-2014.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile1 = options.inputfile1
inputfile2 = options.inputfile2
cropname   = options.cropname
outputfile = options.outputfile

# load crop progress data
cp = CropProgressCountyAdapter(inputfile1, inputfile2, cropname)
years, counties, per = cp.year, cp.county, cp.per
planting = cp.getVar('planting')
anthesis = cp.getVar('anthesis')
maturity = cp.getVar('maturity')

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = years - years[0]
    yearsvar.units = 'years since %d' % years[0]
    yearsvar.long_name = 'time'

    f.createDimension('county', len(counties))
    countyvar = f.createVariable('county', 'i4', 'county')
    countyvar[:] = counties
    countyvar.units = 'county number'
    countyvar.long_name = 'county'

    f.createDimension('per', len(per))
    pervar = f.createVariable('per', 'i4', 'per')
    pervar[:] = per
    pervar.units = '%'
    pervar.long_name = 'percentage'

    pvar = f.createVariable('planting', 'f4', ('time', 'county', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    pvar[:] = planting
    pvar.units = 'julian day'
    pvar.long_name = 'planting'

    avar = f.createVariable('anthesis', 'f4', ('time', 'county', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = anthesis
    avar.units = 'julian day'
    avar.long_name = 'anthesis'

    mvar = f.createVariable('maturity', 'f4', ('time', 'county', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = maturity
    mvar.units = 'julian day'
    mvar.long_name = 'maturity'