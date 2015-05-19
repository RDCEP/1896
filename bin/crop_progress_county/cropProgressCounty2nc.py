#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from CropProgressCountyAdapter import CropProgressCountyAdapterComposite

# parse inputs
parser = OptionParser()
parser.add_option("--inputfile1", dest = "inputfile1", default = "out_2009-2013.final.nc4", type = "string",
                  help = "Input netcdf file for 2009-2013", metavar = "FILE")
parser.add_option("--inputfile2", dest = "inputfile2", default = "out_2014.final.nc4", type = "string",
                  help = "Input netcdf file for 2014", metavar = "FILE")
parser.add_option("-c", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-a", "--careafile", dest = "careafile", default = "maize.county.nc4", type = "string",
                  help = "County-level area file", metavar = "FILE")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-v", "--variables", dest = "variables", default = "planting,anthesis,maturity", type = "string",
                  help = "Comma-separated list of variables to process")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.2009-2014.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile1 = options.inputfile1
inputfile2 = options.inputfile2
cmapfile   = options.cmapfile
careafile  = options.careafile
cropname   = options.cropname
variables  = options.variables
outputfile = options.outputfile

variables = variables.split(',')

# load crop progress data
cp = CropProgressCountyAdapterComposite(inputfile1, inputfile2, cmapfile, careafile, cropname)
years, counties, per = cp.year, cp.county, cp.per

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

    for i in range(len(variables)):
        vvar = f.createVariable(variables[i], 'f4', ('time', 'county', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
        vvar[:] = cp.getCountyVar(variables[i])
        vvar.units = 'julian day'
        vvar.long_name = variables[i]