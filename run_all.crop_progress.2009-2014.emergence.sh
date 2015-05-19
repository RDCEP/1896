#!/bin/bash

PATH=$PATH:utils

for c in maize; do # just maize for now
    echo Running $c

    finalfile=data/$c/final/$c.crop_progress.2009-2014.emergence.nc4

    bin/crop_progress_county/downscaleCropProgressCountyEmergence.py --inputfile1 data/common/crop_progress.2009-2013.nc4 \
                                                                     --inputfile2 data/common/crop_progress.2014.nc4      \
                                                                     -c data/common/USA_adm_all_fips.nc4                  \
                                                                     -a data/$c/aux/$c.county.nc4                         \
                                                                     -m data/$c/aux/$c.mask.0.01.nc4                      \
                                                                     -n $c                                                \
                                                                     -o $finalfile
    bin/crop_progress_county/fillGaps.py -i $finalfile                   \
                                         -m data/$c/aux/$c.mask.0.01.nc4 \
                                         -o $finalfile.2
    mv $finalfile.2 $finalfile
done