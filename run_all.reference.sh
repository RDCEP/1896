#!/bin/bash

PATH=$PATH:utils

# create county-level reference files
for c in maize soybean sorghum cotton-upland cotton-pima barley rapeseed; do
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

# handle special case of wheat separately
crop=wheat
for c in wheat.spring wheat.winter; do
   echo Running county-level $c . . .
   bin/reference/reference2nc.py -y data/$crop/reference/$c.yield.csv,data/$crop/reference/$c.yield_irr.csv                   \
                                 -a data/$crop/reference/$c.harvested_area.csv,data/$crop/reference/$c.harvested_area_irr.csv \
                                 -s data/$crop/reference/$c.census_areas.csv                                                  \
                                 -t 1980,2012                                                                                 \
                                 -n $c                                                                                        \
                                 -o data/$crop/final/$c.reference.county.nc4
done

# combine cotton files
echo Combining cotton crops . . .
bin/reference/combineCotton.py -c data/cotton/final/cotton-upland.reference.county.nc4 \
                               -p data/cotton/final/cotton-pima.reference.county.nc4   \
                               -o data/cotton/final/cotton.reference.county.nc4

# downscale to grid level
for c in maize soybean sorghum cotton barley rapeseed; do
   echo Running grid-level $c . . .
   bin/reference/downscaleWithMIRCA.py -i data/$c/final/$c.reference.county.nc4 \
                                       -a data/$c/aux/$c.NA.nc4                 \
                                       -c data/$c/aux/$c.county.nc4             \
                                       -f data/common/USA_adm_all_fips.nc4      \
                                       -m data/$c/aux/$c.mask.0.01.nc4          \
                                       -o data/$c/final/$c.reference.nc4
   bin/reference/fillGaps.py -i data/$c/final/$c.reference.nc4   \
                             -m data/$c/aux/$c.mask.0.01.nc4     \
                             -o data/$c/final/$c.reference.nc4.2
   mv data/$c/final/$c.reference.nc4.2 data/$c/final/$c.reference.nc4
done

# handle special case of wheat separately
crop=wheat
for c in wheat.spring wheat.winter; do
   echo Running grid-level $c . . .
   bin/reference/downscaleWithMIRCA.py -i data/$crop/final/$c.reference.county.nc4  \
                                       -a data/$crop/aux/$crop.NA.nc4               \
                                       -c data/$crop/aux/$crop.county.nc4           \
                                       -f data/common/USA_adm_all_fips.nc4          \
                                       -m data/$crop/aux/$crop.mask.0.01.nc4        \
                                       -o data/$crop/final/$c.reference.nc4
   bin/reference/fillGaps.py -i data/$crop/final/$c.reference.nc4   \
                             -m data/$crop/aux/$crop.mask.0.01.nc4  \
                             -o data/$crop/final/$c.reference.nc4.2
   mv data/$crop/final/$c.reference.nc4.2 data/$crop/final/$c.reference.nc4
done

# combine wheat
bin/reference/combineWheat.py -s data/wheat/final/wheat.spring.reference.nc4 \
                              -w data/wheat/final/wheat.winter.reference.nc4 \
                              -o data/wheat/final/wheat.reference.nc4        \
                              -m data/wheat/final/wheat.variety.mask.nc4
