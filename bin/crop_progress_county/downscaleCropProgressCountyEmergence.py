#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, masked_where
from numpy import zeros, ones, logical_not, unique, resize, array, where
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
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.2009-2014.emergence.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile1 = options.inputfile1
inputfile2 = options.inputfile2
cmapfile   = options.cmapfile
careafile  = options.careafile
maskfile   = options.maskfile
cropname   = options.cropname
outputfile = options.outputfile

# load crop progress data
cp = CropProgressCountyAdapterComposite(inputfile1, inputfile2, cmapfile, careafile, cropname)
years, counties, states, per = cp.year, cp.county, cp.state, cp.per
cemergence, semergence = cp.getCountyVar('emergence'), cp.getStateVar('emergence')

# load county map
with nc(cmapfile) as f:
    clats, clons = f.variables['lat'][:], f.variables['lon'][:]
    cmap = f.variables['county'][:]
    smap = f.variables['state'][:]

# mask counties without data
ucounties = unique(cmap)
ucounties = ucounties[~ucounties.mask]
for i in range(len(ucounties)):
    if not ucounties[i] in counties:
        cmap = masked_where(cmap == ucounties[i], cmap)

# mask states without data
ustates = unique(smap)
ustates = ustates[~ustates.mask]
for i in range(len(ustates)):
    if not ustates[i] in states:
        smap = masked_where(smap == ustates[i], smap)

# get lat/lon map
latd = resize(clats, (len(clons), len(clats))).T
lond = resize(clons, (len(clats), len(clons)))

# convert to 1D arrays
latdc = latd[~cmap.mask]
londc = lond[~cmap.mask]
cmap  = array(cmap[~cmap.mask])
latds = latd[~smap.mask]
londs = lond[~smap.mask]
smap  = array(smap[~smap.mask])

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale to grid level
nyears, nlats, nlons, nper = len(years), len(mlats), len(mlons), len(per)
sh = (nyears, nlats, nlons, nper)
cdemergence = masked_array(zeros(sh), mask = ones(sh))
sdemergence = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)): # iterate over points
    l1, l2 = latidx[i], lonidx[i]

    # find closest county
    totd = (latdc - mlats[l1]) ** 2 + (londc - mlons[l2]) ** 2
    cidx = where(counties == cmap[totd.argmin()])[0][0]

    # find closest state
    totd = (latds - mlats[l1]) ** 2 + (londs - mlons[l2]) ** 2
    sidx = where(states == smap[totd.argmin()])[0][0]

    cdemergence[:, l1, l2] = cemergence[:, cidx]
    sdemergence[:, l1, l2] = semergence[:, sidx]

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
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

    ecvar = f.createVariable('emergence', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    ecvar[:] = cdemergence
    ecvar.units = 'julian day'
    ecvar.long_name = 'emergence'

    esvar = f.createVariable('emergence_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    esvar[:] = sdemergence
    esvar.units = 'julian day'
    esvar.long_name = 'emergence'