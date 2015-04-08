#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from Census import CensusData
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, masked_where
from numpy import zeros, ones, unique, arange, array, resize, where, logical_not

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.census_areas.csv", type = "string",
                  help = "Input CSV file", metavar = "FILE")
parser.add_option("-c", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.census.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
cmapfile   = options.cmapfile
maskfile   = options.maskfile
trange     = options.trange
cropname   = options.cropname
outputfile = options.outputfile

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

# load census data
census    = CensusData(inputfile, cropname)
counties  = census.counties
cfracarea = census.getFrac(years)

# load county map
with nc(cmapfile) as f:
    clats, clons = f.variables['lat'][:], f.variables['lon'][:]
    cmap = f.variables['county'][:]

# mask counties without data
ucounties = unique(cmap)
ucounties = ucounties[~ucounties.mask]
for i in range(len(ucounties)):
    if not ucounties[i] in counties:
        cmap = masked_where(cmap == ucounties[i], cmap)

# get lat/lon map
latd = resize(clats, (len(clons), len(clats))).T
lond = resize(clons, (len(clats), len(clons)))

# convert to 1D arrays
latd = latd[~cmap.mask]
lond = lond[~cmap.mask]
cmap = array(cmap[~cmap.mask])

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale to grid level
nyears, nlats, nlons = len(years), len(mlats), len(mlons)
sh = (nyears, nlats, nlons)
fracarea = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    # find closest county with data
    totd = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    cidx = where(counties == cmap[totd.argmin()])[0][0]

    fracarea[:, l1, l2] = cfracarea[:, cidx]

with nc(outputfile, 'w') as f:
    f.createDimension('time', nyears)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = years - years[0]
    yearsvar.units = 'years since %d' % years[0]
    yearsvar.long_name = 'time'

    f.createDimension('lat', nlats)
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = mlats
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', nlons)
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = mlons
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    fvar = f.createVariable('frac_area', 'f4', ('time', 'lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    fvar[:] = fracarea
    fvar.units = ''
    fvar.long_name = 'irrigated area / total area'