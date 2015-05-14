#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from numpy import resize
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import where, masked_where, logical_and

# parse inputs
parser = OptionParser()
parser.add_option("-s", "--springfile", dest = "springfile", default = "wheat.spring.reference.nc4", type = "string",
                  help = "Spring wheat reference file", metavar = "FILE")
parser.add_option("-w", "--winterfile", dest = "winterfile", default = "wheat.winter.reference.nc4", type = "string",
                  help = "Winter wheat reference file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "wheat.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "wheat.variety.mask.nc4", type = "string",
                  help = "Output wheat variety mask netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

springfile = options.springfile
winterfile = options.winterfile
outputfile = options.outputfile
maskfile   = options.maskfile

with nc(springfile) as f:
    time      = f.variables['time'][:]
    tunits    = f.variables['time'].units
    lat, lon  = f.variables['lat'][:], f.variables['lon'][:]
    irr       = f.variables['irr'][:]
    yld1      = f.variables['yield'][:]
    area1     = f.variables['area'][:]
    marea1    = f.variables['area_mirca'][:]

with nc(winterfile) as f:
    yld2   = f.variables['yield'][:]
    area2  = f.variables['area'][:]
    marea2 = f.variables['area_mirca'][:]

a1 = area1[20 : 31, :, :, 2].mean(axis = 0) # sum, averaged from 2000-2010
a2 = area2[20 : 31, :, :, 2].mean(axis = 0)

latd = resize(lat, (len(lon), len(lat))).T
latd = masked_where(a1.mask, latd)

latidx, lonidx = where(logical_and(a2 > a1, latd <= 49)) # replace with winter wheat if area is greater AND lat <= 49

yldf   = yld1.copy()
areaf  = area1.copy()
mareaf = marea1.copy()

yldf[:, latidx, lonidx, :]   = yld2[:, latidx, lonidx, :]
areaf[:, latidx, lonidx, :]  = area2[:, latidx, lonidx, :]
mareaf[:, latidx, lonidx, :] = marea2[:, latidx, lonidx, :]

dvar = a1.copy()
dvar[:] = 1
dvar[logical_and(a1 < a2, latd <= 49)] = 2
dvar = masked_where(a1.mask, dvar)

with nc(outputfile, 'w') as f:
    f.createDimension('time', None)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time
    yearsvar.units = tunits
    yearsvar.long_name = 'time'

    f.createDimension('lat', len(lat))
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lat
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', len(lon))
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lon
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    f.createDimension('irr', len(irr))
    irrvar = f.createVariable('irr', 'i4', 'irr')
    irrvar[:] = irr
    irrvar.units = 'ir, rf, sum'
    irrvar.long_name = 'mapping'

    yldvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yldvar[:] = yldf
    yldvar.units = 'kg/ha'
    yldvar.long_name = 'harvested yield'

    areavar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    areavar[:] = areaf
    areavar.units = 'ha'
    areavar.long_name = 'harvested area'

    mareavar = f.createVariable('area_mirca', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    mareavar[:] = mareaf
    mareavar.units = 'ha'
    mareavar.long_name = 'harvested area'

with nc(maskfile, 'w') as f:
    f.createDimension('lat', len(lat))
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = lat
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', len(lon))
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = lon
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    dvarvar = f.createVariable('variety', 'f4', ('lat', 'lon'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    dvarvar[:] = dvar
    dvarvar.units = 'mapping'
    dvarvar.long_name = 'spring, winter'