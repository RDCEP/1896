#!/bin/bash

PATH=$PATH:utils

# create county-level reference files
for c in maize soybean sorghum cotton-upland cotton-pima; do
   echo Running county-level $c . . .
   if [ $c = cotton-upland ] || [ $c = cotton-pima ]; then
      crop=cotton
   else
      crop=$c
   fi
   bin/reference/reference2nc.py -y data/$crop/reference/$crop.yield.csv,data/$crop/reference/$crop.yield_irr.csv                   \
                                 -a data/$crop/reference/$crop.harvested_area.csv,data/$crop/reference/$crop.harvested_area_irr.csv \
                                 -s data/$crop/reference/$crop.census_areas.csv                                                     \
                                 -t 1980,2012                                                                                       \
                                 -n $c                                                                                              \
                                 -o data/$crop/final/$c.reference.county.nc4
done

# combine cotton files
echo Combining cotton crops . . .
bin/reference/combineCotton.py -c data/cotton/final/cotton-upland.reference.county.nc4 \
                               -p data/cotton/final/cotton-pima.reference.county.nc4   \
                               -o data/cotton/final/cotton.reference.county.nc4

# downscale to grid level
for c in maize soybean sorghum cotton; do
   echo Running grid-level $c . . .
   bin/reference/downscaleWithMIRCA.py -i data/$c/final/$c.reference.county.nc4  \
                                       -a data/$c/aux/$c.NA.nc4                  \
                                       -c data/$c/aux/$c.county.nc4              \
                                       -f data/common/USA_adm_all_fips.nc4       \
                                       -m data/$c/aux/$c.mask.0.01.nc4           \
                                       -o data/$c/final/$c.reference.nc4
done