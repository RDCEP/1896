#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array
from numpy import ones, zeros, where, resize

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "barley.canada.reference.province.nc4", type = "string",
                  help = "Province-level reference netcdf4 file", metavar = "FILE")
parser.add_option("-g", "--griddedfile", dest = "griddedfile", default = "barley.spam.nc4", type = "string",
                  help = "Gridded yield and area file", metavar = "FILE")
parser.add_option("-a", "--aggfile", dest = "aggfile", default = "barley.spam.province.nc4", type = "string",
                  help = "Aggregated yield and area file", metavar = "FILE")
parser.add_option("-p", "--provincefile", dest = "provincefile", default = "canada.pronvinces.NA.nc4", type = "string",
                  help = "Province mapping file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "barley.canada.mask.0.01.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-t", "--trange", dest = "trange", default = "1980-2012", type = "string",
                  help = "Time range (tstart-tend)")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "barley.canada.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile    = options.inputfile
griddedfile  = options.griddedfile
aggfile      = options.aggfile
provincefile = options.provincefile
maskfile     = options.maskfile
trange       = options.trange
outputfile   = options.outputfile

tstart, tend = [int(t) for t in trange.split('-')]
ntimes       = tend - tstart + 1

# load province-level reference data
with nc(inputfile) as f:
    time       = f.variables['time'][:]
    tunits     = f.variables['time'].units
    rprovinces = f.variables['province'][:]
    ryld       = f.variables['yield'][:]
    rarea      = f.variables['area'][:]

time += int(findall(r'\d+', tunits)[0])

tidx0, tidx1 = where(time == tstart)[0][0], where(time == tend)[0][0] + 1
ryld  = ryld[tidx0  : tidx1]
rarea = rarea[tidx0 : tidx1]

# load gridded file
with nc(griddedfile) as f:
    lats, lons      = f.variables['lat'][:], f.variables['lon'][:]
    area_gridded    = masked_array(zeros((3, len(lats), len(lons))), mask = ones((3, len(lats), len(lons))))
    yld_gridded     = masked_array(zeros((3, len(lats), len(lons))), mask = ones((3, len(lats), len(lons))))
    area_gridded[0] = f.variables['area_irrigated'][:]
    area_gridded[1] = f.variables['area_rainfed'][:]
    area_gridded[2] = f.variables['area_sum'][:]
    yld_gridded[0]  = f.variables['yield_irrigated'][:]
    yld_gridded[1]  = f.variables['yield_rainfed'][:]
    yld_gridded[2]  = f.variables['yield_sum'][:]

latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))
latidx, lonidx = where(~area_gridded[0].mask)
latd = latd[latidx, lonidx]
lond = lond[latidx, lonidx]
area_gridded = area_gridded[:, latidx, lonidx]
yld_gridded  = yld_gridded[:,  latidx, lonidx]

# load aggregated file
with nc(aggfile) as f:
    aprovinces = f.variables['province'][:]
    area_agg   = f.variables['area'][:]
    yld_agg    = f.variables['yield'][:]

# load province map file
with nc(provincefile) as f:
    pmap = f.variables['province'][:]

# load mask file
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask         = f.variables['mask'][:]
latidx, lonidx = where(~mask.mask)

nlats, nlons, nirr = len(mlats), len(mlons), 3

# downscale to grid level
yld  = masked_array(zeros((ntimes, nlats, nlons, nirr)), mask = ones((ntimes, nlats, nlons, nirr)))
area = masked_array(zeros((ntimes, nlats, nlons, nirr)), mask = ones((ntimes, nlats, nlons, nirr)))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    llidx = ((latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2).argmin()

    pidx1 = where(rprovinces == pmap[l1, l2])[0][0]
    pidx2 = where(aprovinces == pmap[l1, l2])[0][0]

    # downscale yield and area
    for j in range(nirr):
        if yld_agg[pidx2]:
            yld[:, l1, l2, j] = yld_gridded[j, llidx] * ryld[:, pidx1] / yld_agg[pidx2]
        if area_agg[pidx2]:
            area[:, l1, l2, j] = area_gridded[j, llidx] * rarea[:, pidx1] / area_agg[pidx2]

with nc(outputfile, 'w') as f:
    f.createDimension('time', ntimes)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = range(ntimes)
    yearsvar.units = 'years since %d' % tstart
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
    ivar.long_name = 'ir, rf, sum'

    yvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yvar[:] = yld
    yvar.units = 'kg/ha'
    yvar.long_name = 'harvested yield'

    avar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = area
    avar.units = 'ha'
    avar.long_name = 'harvested area'