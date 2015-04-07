#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy import zeros, arange, interp
from CropProgress import CropProgressData

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.all.dates.csv", type = "string",
                  help = "Input CSV file", metavar = "FILE")
parser.add_option("-d", "--sdistfile", dest = "sdistfile", default = "state_distances.csv", type = "string",
                  help = "State distances file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
sdistfile  = options.sdistfile
trange     = options.trange
cropname   = options.cropname
outputfile = options.outputfile

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

# load crop progress data
cp = CropProgressData(inputfile, sdistfile, cropname)
states, per = cp.states, cp.per
planting = cp.getVar('planting')
anthesis = cp.getVar('anthesis')
maturity = cp.getVar('maturity')

# extrapolate in time
pltinter = zeros((len(years), len(states), len(per)))
antinter = zeros((len(years), len(states), len(per)))
matinter = zeros((len(years), len(states), len(per)))
for i in range(len(states)):
    for j in range(len(per)):
        pltinter[:, i, j] = interp(years, cp.years, planting[:, i, j])
        antinter[:, i, j] = interp(years, cp.years, anthesis[:, i, j])
        matinter[:, i, j] = interp(years, cp.years, maturity[:, i, j])

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = years - years[0]
    yearsvar.units = 'years since %d' % years[0]
    yearsvar.long_name = 'time'

    f.createDimension('state', len(states))
    statevar = f.createVariable('state', 'i4', 'state')
    statevar[:] = states
    statevar.units = 'state number'
    statevar.long_name = 'state'

    f.createDimension('per', len(per))
    pervar = f.createVariable('per', 'i4', 'per')
    pervar[:] = per
    pervar.units = '%'
    pervar.long_name = 'percentage'

    pvar = f.createVariable('planting', 'f4', ('time', 'state', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    pvar[:] = pltinter
    pvar.units = 'julian day'
    pvar.long_name = 'planting'

    avar = f.createVariable('anthesis', 'f4', ('time', 'state', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = antinter
    avar.units = 'julian day'
    avar.long_name = 'anthesis'

    mvar = f.createVariable('maturity', 'f4', ('time', 'state', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = matinter
    mvar.units = 'julian day'
    mvar.long_name = 'maturity'