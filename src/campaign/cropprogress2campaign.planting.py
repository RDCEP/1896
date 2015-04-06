#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array
from datetime import datetime, timedelta
from numpy import where, resize, logical_not, zeros, ones, array

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.crop_progress.nc4", type = "string",
                  help = "Input crop progress netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "all.mask.0.05.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("--wlat", dest = "wlat", default = 1, type = "float",
                  help = "Weight assigned to latitude in distance metric")
parser.add_option("--wlon", dest = "wlon", default = 1, type = "float",
                  help = "Weight assigned to longitude in distance metric")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.planting.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
maskfile   = options.maskfile
wlat       = options.wlat
wlon       = options.wlon
outputfile = options.outputfile

with nc(inputfile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    time       = f.variables['time'][:]
    tunits     = f.variables['time'].units
    plt        = f.variables['planting'][:, :, :, 2] # 50th percentile

time  += int(findall(r'\d+', tunits)[0])
dtimes = [datetime(time[t], 1, 1) for t in range(len(time))]

vmask = plt[0].mask
latidx, lonidx = where(~vmask)

# get lat/lon map
latd = resize(lats, (len(lons), len(lats))).T
lond = resize(lons, (len(lats), len(lons)))

# convert to 1D arrays
latd = latd[latidx, lonidx]
lond = lond[latidx, lonidx]
plt  = array(plt[:, latidx, lonidx])

# convert to YYYYMMDD
plt2 = zeros(plt.shape, dtype = int)
for i in range(len(latidx)):
    jday = plt[:, i]
    plt2[:, i] = [int((dtimes[j] + timedelta(int(jday[j] - 1))).strftime('%Y%m%d')) for j in range(len(dtimes))]

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale
nyears, nlats, nlons = len(time), len(mlats), len(mlons)
plt3 = masked_array(zeros((nyears, nlats, nlons)), mask = ones((nyears, nlats, nlons)), dtype = int)
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]
    totd = wlat * (latd - mlats[l1]) ** 2 + wlon * (lond - mlons[l2]) ** 2
    x = totd.argmin()
    plt3[:, l1, l2] = plt2[:, totd.argmin()]

with nc(outputfile, 'w') as f:
    f.createDimension('time', nyears)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time - time[0]
    yearsvar.units = tunits
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

    pvar = f.createVariable('planting', 'i4', ('time', 'lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 999999)
    pvar[:] = plt3
    pvar.units = 'YYYYMMDD'
    pvar.long_name = 'planting'