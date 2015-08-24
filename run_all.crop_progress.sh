#!/bin/bash

PATH=$PATH:utils

for c in maize soybean sorghum cotton wheat.spring wheat.winter barley; do
   echo Running $c . . .
   if [ $c = wheat.spring ] || [ $c = wheat.winter ]; then
      crop=wheat
   else
      crop=$c
   fi

   finalfile=data/$crop/final/$c.crop_progress.nc4

   bin/crop_progress/downscaleCropProgress.py -i data/$crop/reference/$crop.all.dates.csv \
                                              -d data/common/state_distances.csv          \
                                              -s data/common/USA_adm_all_fips.nc4         \
                                              -m data/$crop/aux/$c.mask.0.01.nc4          \
                                              -t 1980,2012                                \
                                              -n $c                                       \
					      --average_canada                            \
                                              -o $finalfile
   bin/crop_progress_county/fillGaps.py -i $finalfile                      \
                                        -m data/$crop/aux/$c.mask.0.01.nc4 \
                                        -o $finalfile.2
   mv $finalfile.2 $finalfile
done
