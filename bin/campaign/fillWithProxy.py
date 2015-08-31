#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "swh.file.nc4", type = "string",
                  help = "Input netcdf4 file", metavar = "FILE")
parser.add_option("-p", "--proxyfile", dest = "proxyfile", default = "wwh.file.nc4", type = "string",
                  help = "Proxy netcdf4 file", metavar = "FILE")
parser.add_option("-v", "--variables", dest = "variables", default = "p1,p2,p3", type = "string",
                  help = "Comma-separated list of variables")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "filled.swh.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
proxyfile  = options.proxyfile
variables  = options.variables
outputfile = options.outputfile

variables = variables.split(',')

copyfile(inputfile, outputfile)

fi = nc(inputfile)
fp = nc(proxyfile)

with nc(outputfile, 'a') as fo:
    for i in range(len(variables)):
        vi = fi.variables[variables[i]][:]
        vp = fp.variables[variables[i]][:]

        vi[vi.mask] = vp[vi.mask] # replace with proxy

        vo = fo.variables[variables[i]]
        vo[:] = vi

fi.close()
fp.close()