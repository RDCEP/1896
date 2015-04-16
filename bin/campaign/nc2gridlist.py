#!/usr/bin/env python

# import modules
from numpy.ma import where
from netCDF4 import Dataset as nc
from optparse import OptionParser
from numpy import floor, zeros, unique

def globalindex(lat, lon, lat_delta, lon_delta):
    glatidx = int(floor((90 - lat) / lat_delta)) + 1
    glonidx = int(floor((lon + 180) / lon_delta)) + 1
    return glatidx, glonidx

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.mask.0.01.nc4", type = "string",
                  help = "Input mask netCDF file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.gridlist.0.01.txt", type = "string",
                  help = "Output gridlist file", metavar = "FILE")
options, args = parser.parse_args()

inputfile  = options.inputfile
outputfile = options.outputfile

with nc(inputfile) as f:
    lat, lon = f.variables['lat'][:], f.variables['lon'][:]
    mask     = f.variables['mask'][:]

lat_delta, lon_delta = abs(lat[0] - lat[1]), abs(lon[0] - lon[1])
lat_idx, lon_idx = where(~mask.mask)

grid_list = open(outputfile, 'w')
grid_vals = zeros(len(lat_idx))
for i in range(len(lat_idx)):
    latp, lonp = lat[lat_idx[i]], lon[lon_idx[i]]
    glat, glon = globalindex(latp, lonp, lat_delta, lon_delta)
    grid_list.write('%d/%d\n' % (glat, glon))
    grid_vals[i] = 10000 * glat + glon
grid_list.close()

if len(unique(grid_vals)) != len(grid_vals): print 'Redundancy!'