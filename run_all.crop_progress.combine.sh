#!/bin/bash

PATH=$PATH:utils

for c in maize soybean sorghum cotton; do
    echo Running $c . . .

    file1=data/$c/final/$c.crop_progress.nc4 # 1980-2012
    file2=data/$c/final/$c.crop_progress.2009-2014.nc4 # 2009-2014
    resfile=data/$c/final/$c.crop_progress.2009-2014.residuals.nc4
    finalfile=data/$c/final/$c.crop_progress.1980-2014.nc4

    cp $file1 crop_progress1.nc4
    cp $file2 crop_progress2.nc4

    # average county residuals
    ncwa -h -a time $resfile residuals.nc4
    ncks -O -h -v planting_dev,anthesis_dev,maturity_dev residuals.nc4 residuals.nc4

    # add residuals to state data
    ncks -h -A residuals.nc4 crop_progress1.nc4
    ncap2 -O -h -s "planting=planting+planting_dev" crop_progress1.nc4 crop_progress1.nc4
    ncap2 -O -h -s "anthesis=anthesis+anthesis_dev" crop_progress1.nc4 crop_progress1.nc4
    ncap2 -O -h -s "maturity=maturity+maturity_dev" crop_progress1.nc4 crop_progress1.nc4
    ncks -O -h -x -v planting_dev,anthesis_dev,maturity_dev crop_progress1.nc4 crop_progress1.nc4

    # combine files
    ncks -O -h -d time,0,28 crop_progress1.nc4 crop_progress1.nc4
    ncks -O -h --mk_rec_dim time crop_progress1.nc4 crop_progress1.nc4
    ncks -O -h -x -v planting_state,anthesis_state,maturity_state crop_progress2.nc4 crop_progress2.nc4
    ncatted -O -h -a units,time,m,c,"years since 1980" crop_progress2.nc4 crop_progress2.nc4
    ncap2 -O -h -s "time=time+29" crop_progress2.nc4 crop_progress2.nc4
    ncrcat -O -h crop_progress1.nc4 crop_progress2.nc4 $finalfile
    nccopy -d9 -k4 $finalfile $finalfile.2
    mv $finalfile.2 $finalfile

    rm residuals.nc4 crop_progress1.nc4 crop_progress2.nc4
done