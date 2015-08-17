#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, masked_where
from numpy import zeros, ones, logical_and, unique, resize, array, where
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
parser.add_option("--average_canada", action = "store_true", dest = "avecan", default = False,
                  help = "Whether to average northern latitudes to fill Canada")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.crop_progress.2009-2014.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile1 = options.inputfile1
inputfile2 = options.inputfile2
cmapfile   = options.cmapfile
careafile  = options.careafile
maskfile   = options.maskfile
cropname   = options.cropname
avecan     = options.avecan
outputfile = options.outputfile

# load crop progress data
cp = CropProgressCountyAdapterComposite(inputfile1, inputfile2, cmapfile, careafile, cropname)
years, counties, states, per = cp.year, cp.county, cp.state, cp.per
cplanting, splanting = cp.getCountyVar('planting'), cp.getStateVar('planting')
canthesis, santhesis = cp.getCountyVar('anthesis'), cp.getStateVar('anthesis')
cmaturity, smaturity = cp.getCountyVar('maturity'), cp.getStateVar('maturity')

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
if avecan:
    mlatd = resize(mlats, (len(mlons), len(mlats))).T
    latidx, lonidx = where(logical_and(~mask.mask, mlatd <= 49))
else:
    latidx, lonidx = where(~mask.mask)

# downscale to grid level
nyears, nlats, nlons, nper = len(years), len(mlats), len(mlons), len(per)
sh = (nyears, nlats, nlons, nper)
cdplanting = masked_array(zeros(sh), mask = ones(sh))
cdanthesis = masked_array(zeros(sh), mask = ones(sh))
cdmaturity = masked_array(zeros(sh), mask = ones(sh))
sdplanting = masked_array(zeros(sh), mask = ones(sh))
sdanthesis = masked_array(zeros(sh), mask = ones(sh))
sdmaturity = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)): # iterate over points
    l1, l2 = latidx[i], lonidx[i]

    # find closest county
    totd = (latdc - mlats[l1]) ** 2 + (londc - mlons[l2]) ** 2
    cidx = where(counties == cmap[totd.argmin()])[0][0]

    # find closest state
    totd = (latds - mlats[l1]) ** 2 + (londs - mlons[l2]) ** 2
    sidx = where(states == smap[totd.argmin()])[0][0]

    cdplanting[:, l1, l2] = cplanting[:, cidx]
    cdanthesis[:, l1, l2] = canthesis[:, cidx]
    cdmaturity[:, l1, l2] = cmaturity[:, cidx]
    sdplanting[:, l1, l2] = splanting[:, sidx]
    sdanthesis[:, l1, l2] = santhesis[:, sidx]
    sdmaturity[:, l1, l2] = smaturity[:, sidx]

if avecan:
    latidx1, lonidx1 = where(logical_and(~mask.mask, logical_and(mlatd >= 48.5, mlatd <= 49)))
    latidx2, lonidx2 = where(logical_and(~mask.mask, mlatd > 49))
    cpcan = cdplanting[:, latidx1, lonidx1].mean(axis = 1)
    cacan = cdanthesis[:, latidx1, lonidx1].mean(axis = 1)
    cmcan = cdmaturity[:, latidx1, lonidx1].mean(axis = 1)
    spcan = sdplanting[:, latidx1, lonidx1].mean(axis = 1)
    sacan = sdanthesis[:, latidx1, lonidx1].mean(axis = 1)
    smcan = sdmaturity[:, latidx1, lonidx1].mean(axis = 1)
    for i in range(len(latidx2)):
        l1, l2 = latidx2[i], lonidx2[i]
        cdplanting[:, l1, l2] = cpcan
        cdanthesis[:, l1, l2] = cacan
        cdmaturity[:, l1, l2] = cmcan
        sdplanting[:, l1, l2] = spcan
        sdanthesis[:, l1, l2] = sacan
        sdmaturity[:, l1, l2] = smcan

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

    pcvar = f.createVariable('planting', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    pcvar[:] = cdplanting
    pcvar.units = 'julian day'
    pcvar.long_name = 'planting'

    acvar = f.createVariable('anthesis', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    acvar[:] = cdanthesis
    acvar.units = 'julian day'
    acvar.long_name = 'anthesis'

    mcvar = f.createVariable('maturity', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mcvar[:] = cdmaturity
    mcvar.units = 'julian day'
    mcvar.long_name = 'maturity'

    psvar = f.createVariable('planting_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    psvar[:] = sdplanting
    psvar.units = 'julian day'
    psvar.long_name = 'planting'

    asvar = f.createVariable('anthesis_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    asvar[:] = sdanthesis
    asvar.units = 'julian day'
    asvar.long_name = 'anthesis'

    msvar = f.createVariable('maturity_state', 'f4', ('time', 'lat', 'lon', 'per'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    msvar[:] = sdmaturity
    msvar.units = 'julian day'
    msvar.long_name = 'maturity'