#!/bin/bash

PATH=$PATH:utils

for c in maize soybean sorghum cotton; do
   echo Running $c . . .
   bin/crop_progress/downscaleCropProgress.py -i data/$c/reference/$c.all.dates.csv \
                                              -d data/common/state_distances.csv    \
                                              -s data/common/USA_adm_all_fips.nc4   \
                                              -m data/$c/aux/$c.mask.0.01.nc4       \
                                              -t 1980,2012                          \
                                              -n $c                                 \
                                              -o data/$c/final/$c.crop_progress.nc4
done