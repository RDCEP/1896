#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from numpy import where, median
from optparse import OptionParser
from netCDF4 import Dataset as nc

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "p5.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-v", "--variable", dest = "variable", default = "cult_p1", type = "string",
                  help = "Variable name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "p5.filtered.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
variable   = options.variable
outputfile = options.outputfile

with nc(inputfile) as f:
    var = f.variables[variable][:] # var(time, lat, lon)

latidx, lonidx = where(~var[0].mask)

for i in range(len(latidx)):
    v = var[:, latidx[i], lonidx[i]]

    medv = median(v)
    stdv = v.std()

    v[abs(v - medv) > max(1.5 * stdv, 100)] = medv

    var[:, latidx[i], lonidx[i]] = v

copyfile(inputfile, outputfile)

with nc(outputfile, 'a') as f:
    newv = f.variables[variable]
    newv[:] = var