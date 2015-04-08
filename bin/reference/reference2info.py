#!/usr/bin/env python
# -*- coding: utf-8 -*-

# add paths
import os, sys
for p in os.environ['PATH'].split(':'): sys.path.append(p)

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from Reference import ReferenceCombiner
from numpy.ma import masked_array, masked_where
from numpy import zeros, ones, unique, arange, where, resize, array, logical_not

# parse inputs
parser = OptionParser()
parser.add_option("-y", "--yieldfiles", dest = "yieldfiles", default = "maize.yield.csv,maize.yield_irr.csv", type = "string",
                  help = "Sum and irrigated yield files separated by comma")
parser.add_option("-a", "--hareafiles", dest = "hareafiles", default = "maize.harvested_area.csv,maize.harvested_area_irr.csv", type = "string",
                  help = "Sum and irrigated harvested area files separated by comma")
parser.add_option("-c", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-s", "--censusfile", dest = "censusfile", default = "maize.census_areas.csv", type = "string",
                  help = "Census file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980,2012", type = "string",
                  help = "Time range")
parser.add_option("-n", "--cropname", dest = "cropname", default = "maize", type = "string",
                  help = "Crop name")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

yieldfiles = options.yieldfiles
hareafiles = options.hareafiles
cmapfile   = options.cmapfile
censusfile = options.censusfile
maskfile   = options.maskfile
trange     = options.trange
cropname   = options.cropname
outputfile = options.outputfile

yieldfile, yieldirrfile = yieldfiles.split(',')
hareafile, hareairrfile = hareafiles.split(',')

ymin, ymax = [int(y) for y in trange.split(',')]
years      = arange(ymin, ymax + 1)

# load reference data
ref        = ReferenceCombiner(yieldfile, yieldirrfile, hareafile, hareairrfile, censusfile, cropname)
counties   = ref.counties
irr        = ref.irr
_, chvt = ref.getVar(years)

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
nyears, nlats, nlons, nirr = len(years), len(mlats), len(mlons), len(irr)
sh = (nyears, nlats, nlons, nirr)
yld = masked_array(zeros(sh), mask = ones(sh))
hvt = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    # find closest county with data
    totd = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    cidx = where(counties == cmap[totd.argmin()])[0][0]

    yld[:, l1, l2] = cyld[:, cidx]
    hvt[:, l1, l2] = chvt[:, cidx]

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

    f.createDimension('irr', nirr)
    ivar = f.createVariable('irr', 'i4', 'irr')
    ivar[:] = range(1, 1 + nirr)
    ivar.units = 'mapping'
    ivar.long_name = ', '.join(irr)

    yvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yvar[:] = yld
    yvar.units = 'kg/ha'
    yvar.long_name = 'harvested yield'

    avar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = hvt
    avar.units = 'ha'
    avar.long_name = 'harvested area'