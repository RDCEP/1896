#!/bin/bash

for c in barley rapeseed; do
   echo Running $c . . .
   bin/reference/downscaleCanadaReference.py -i data/$c/final/${c}.canada.reference.province.nc4 \
                                             -g data/$c/aux/${c}.spam.nc4                        \
                                             -a data/$c/aux/${c}.spam.province.nc4               \
                                             -p data/common/canada.provinces.NA.nc4              \
                                             -m data/$c/aux/${c}.canada.mask.0.01.nc4            \
                                             -t 1980-2012                                        \
                                             -o data/$c/final/${c}.canada.reference.nc4

   # add to reference file
python << END
from numpy import where
from netCDF4 import Dataset as nc

canfile = 'data/$c/final/${c}.canada.reference.nc4'
usfile  = 'data/$c/final/${c}.reference.nc4'

yldcan  = nc(canfile).variables['yield'][:]
areacan = nc(canfile).variables['area'][:]

f = nc(usfile, 'a')

yld  = f.variables['yield']
area = f.variables['area']

yldvar  = yld[:]
areavar = area[:]

tidx, latidx, lonidx, irridx = where(~yldcan.mask)
yldvar[tidx, latidx, lonidx, irridx] = yldcan[tidx, latidx, lonidx, irridx]

if '$c' != 'rapeseed':
    tidx, latidx, lonidx, irridx = where(~areacan.mask)
    areavar[tidx, latidx, lonidx, irridx] = areacan[tidx, latidx, lonidx, irridx]

yld[:]  = yldvar
area[:] = areavar

f.close()
END
done
