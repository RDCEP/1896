#!/bin/bash

# create county-level reference files
for c in maize soybean sorghum cotton-upland cotton-pima; do
   echo Running county-level $c . . .
   if [ $c = cotton-upland ] || [ $c = cotton-pima ]; then
      crop=cotton
   else
      crop=$c
   fi
   src/reference/reference2nc.py -y $crop/reference/$crop.yield.csv,$crop/reference/$crop.yield_irr.csv                   \
                                 -a $crop/reference/$crop.harvested_area.csv,$crop/reference/$crop.harvested_area_irr.csv \
                                 -s $crop/reference/$crop.census_areas.csv                                                \
                                 -t 1980,2012                                                                             \
                                 -n $c                                                                                    \
                                 -o $crop/final/$c.reference.county.nc4
done

# combine cotton files
echo Combining cotton crops . . .
src/reference/combineCotton.py -c cotton/final/cotton-upland.reference.county.nc4 \
                               -p cotton/final/cotton-pima.reference.county.nc4   \
                               -o cotton/final/cotton.reference.county.nc4

# downscale to grid level
for c in maize soybean sorghum cotton; do
   echo Running grid-level $c . . .
   src/reference/downscaleWithMIRCA.py -i $c/final/$c.reference.county.nc4  \
                                       -a $c/aux/$c.NA.nc4                  \
                                       -c $c/aux/$c.county.nc4              \
                                       -f common/USA_adm_all_fips.nc4       \
                                       -m $c/aux/$c.mask.0.01.nc4           \
                                       -o $c/final/$c.reference.nc4
done