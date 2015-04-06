#!/bin/bash

for c in maize soybean sorghum cotton; do
   echo Running $c . . .
   src/crop_progress/downscaleCropProgress.py -i $c/reference/$c.all.dates.csv \
                                              -d common/state_distances.csv    \
                                              -s common/USA_adm_all_fips.nc4   \
                                              -m $c/aux/$c.mask.0.01.nc4       \
                                              -t 1980,2012                     \
                                              -n $c                            \
                                              -o $c/final/$c.crop_progress.nc4
done