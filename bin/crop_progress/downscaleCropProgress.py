#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from CropProgress import CropProgressData
from numpy.ma import masked_array, masked_where
from numpy import zeros, ones, logical_and, unique, resize, array, where, arange, interp

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.all.dates.csv", type = "string",
                  help = "Input CSV file", metavar = "FILE")
parser.add_option("-d", "--sdistfile", dest = "sdistfile", default = "state_distances.csv", type = "string",
                  help = "State distances file", metavar = "FILE")
parser.add_option("-s", "--smapfile", dest = "smapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "State mapping file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("--average_canada", action = "store_true", dest = "avecan", default = False,
                  help = "Whether to average northern latitudes to fill Canada")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
sdistfile  = options.sdistfile
smapfile   = options.smapfile
maskfile   = options.maskfile
trange     = options.trange
cropname   = options.cropname
avecan     = options.avecan
outputfile = options.outputfile

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

# load crop progress data
cp = CropProgressData(inputfile, sdistfile, cropname)
states, per = cp.states, cp.per
splanting = cp.getVar('planting')
santhesis = cp.getVar('anthesis')
smaturity = cp.getVar('maturity')

# extrapolate in time
spltinter = zeros((len(years), len(states), len(per)))
santinter = zeros((len(years), len(states), len(per)))
smatinter = zeros((len(years), len(states), len(per)))
for i in range(len(states)):
    for j in range(len(per)):
        spltinter[:, i, j] = interp(years, cp.years, splanting[:, i, j])
        santinter[:, i, j] = interp(years, cp.years, santhesis[:, i, j])
        smatinter[:, i, j] = interp(years, cp.years, smaturity[:, i, j])

# load state map
with nc(smapfile) as f:
    slats, slons = f.variables['lat'][:], f.variables['lon'][:]
    smap = f.variables['state'][:]

# mask states without data
ustates = unique(smap)
ustates = ustates[~ustates.mask]
for i in range(len(ustates)):
    if not ustates[i] in states:
        smap = masked_where(smap == ustates[i], smap)

# get lat/lon map
latd = resize(slats, (len(slons), len(slats))).T
lond = resize(slons, (len(slats), len(slons)))

# convert to 1D arrays
latd = latd[~smap.mask]
lond = lond[~smap.mask]
smap = array(smap[~smap.mask])

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
if avecan:
    mlatd = resize(mlats, (len(mlons), len(mlats))).T
    latidx, lonidx = where(logical_and(~mask.mask, mlatd <= 49))
else:
    latidx, lonidx = where(~mask.mask)

# downscale to grid level
nyears, nlats, nlons, nper = len(years), len(mlats), len(mlons), len(per)
sh = (nyears, nlats, nlons, nper)
planting = masked_array(zeros(sh), mask = ones(sh))
anthesis = masked_array(zeros(sh), mask = ones(sh))
maturity = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    # find closest state with data
    totd = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    sidx = where(states == smap[totd.argmin()])[0][0]

    planting[:, l1, l2] = spltinter[:, sidx]
    anthesis[:, l1, l2] = santinter[:, sidx]
    maturity[:, l1, l2] = smatinter[:, sidx]

if avecan:
    latidx1, lonidx1 = where(logical_and(~mask.mask, logical_and(mlatd >= 48.5, mlatd <= 49)))
    latidx2, lonidx2 = where(logical_and(~mask.mask, mlatd > 49))
    pcan = planting[:, latidx1, lonidx1].mean(axis = 1)
    acan = anthesis[:, latidx1, lonidx1].mean(axis = 1)
    mcan = maturity[:, latidx1, lonidx1].mean(axis = 1)
    for i in range(len(latidx2)):
        l1, l2 = latidx2[i], lonidx2[i]
        planting[:, l1, l2] = pcan
        anthesis[:, l1, l2] = acan
        maturity[:, l1, l2] = mcan

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

    f.createDimension('per', nper)
    pervar = f.createVariable('per', 'i4', 'per')
    pervar[:] = per
    pervar.units = '%'
    pervar.long_name = 'percentage'

    pvar = f.createVariable('planting', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    pvar[:] = planting
    pvar.units = 'julian day'
    pvar.long_name = 'planting'

    avar = f.createVariable('anthesis', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = anthesis
    avar.units = 'julian day'
    avar.long_name = 'anthesis'

    mvar = f.createVariable('maturity', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mvar[:] = maturity
    mvar.units = 'julian day'
    mvar.long_name = 'maturity'