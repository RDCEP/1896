#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy.ma import where
from shutil import copyfile
from optparse import OptionParser
from netCDF4 import Dataset as nc

# parse inputs
parser = OptionParser()
parser.add_option("-s", "--springfile", dest = "springfile", default = "wheat.spring.crop_progress.1980-2014.nc4", type = "string",
                  help = "Spring wheat crop progress file", metavar = "FILE")
parser.add_option("-w", "--winterfile", dest = "winterfile", default = "wheat.winter.crop_progress.1980-2014.nc4", type = "string",
                  help = "Winter wheat crop progress file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "wheat.variety.mask.nc4", type = "string",
                  help = "Wheat variety mask netcdf4 file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "wheat.crop_progress.1980-2014.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

springfile = options.springfile
winterfile = options.winterfile
maskfile   = options.maskfile
outputfile = options.outputfile

copyfile(springfile, outputfile)

with nc(springfile) as f:
    planting1 = f.variables['planting'][:]
    anthesis1 = f.variables['anthesis'][:]
    maturity1 = f.variables['maturity'][:]

with nc(winterfile) as f:
    planting2 = f.variables['planting'][:]
    anthesis2 = f.variables['anthesis'][:]
    maturity2 = f.variables['maturity'][:]

with nc(maskfile) as f:
    mask = f.variables['variety'][:]

latidx, lonidx = where(mask == 2)

plantingf = planting1.copy()
anthesisf = anthesis1.copy()
maturityf = maturity1.copy()

plantingf[:, latidx, lonidx, :] = planting2[:, latidx, lonidx, :]
anthesisf[:, latidx, lonidx, :] = anthesis2[:, latidx, lonidx, :]
maturityf[:, latidx, lonidx, :] = maturity2[:, latidx, lonidx, :]

with nc(outputfile, 'a') as f:
    p = f.variables['planting']
    p[:] = plantingf
    a = f.variables['anthesis']
    a[:] = anthesisf
    m = f.variables['maturity']
    m[:] = maturityf