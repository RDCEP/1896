#!/bin/bash

PATH=$PATH:utils

# create county-level reference files
for c in maize soybean sorghum cotton-upland cotton-pima barley rapeseed alfalfa corn-silage other-hay rice peanuts sugarbeets rye beans; do
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
for c in maize soybean sorghum cotton barley rapeseed alfalfa corn-silage other-hay rice peanuts sugarbeets rye beans; do
   echo Running grid-level $c . . .
   bin/reference/downscaleReference.py -i data/$c/final/$c.reference.county.nc4        \
                                       -a data/$c/aux/$c.NA.nc4                        \
				       -y data/$c/aux/$c.yield.nc4                     \
                                       -c data/$c/aux/$c.county.nc4                    \
                                       -f data/common/USA_CAN_adm_all_fips.US.only.nc4 \
                                       -m data/$c/aux/$c.mask.0.01.nc4                 \
                                       -o data/$c/final/$c.reference.nc4
done

# handle special case of wheat separately
crop=wheat
for c in wheat.spring wheat.winter; do
   echo Running grid-level $c . . .
   bin/reference/downscaleReference.py -i data/$crop/final/$c.reference.county.nc4     \
                                       -a data/$crop/aux/$crop.NA.nc4                  \
                                       -y data/$crop/aux/$crop.yield.nc4               \
                                       -c data/$crop/aux/$crop.county.nc4              \
                                       -f data/common/USA_CAN_adm_all_fips.US.only.nc4 \
                                       -m data/$crop/aux/$c.mask.full.nc4              \
                                       -o data/$crop/final/$c.reference.nc4
done
