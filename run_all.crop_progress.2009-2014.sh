#!/bin/bash

for c in maize soybean sorghum cotton wheat.winter wheat.spring barley; do
    echo Running $c
    if [ $c = wheat.winter ] || [ $c = wheat.spring ]; then
        crop=wheat
    else
        crop=$c
    fi

    finalfile=$crop/final/$c.crop_progress.2009-2014.nc4

    src/crop_progress_county/downscaleCropProgressCounty.py --inputfile1 CPoutput/out_2009-2013.final.nc4 \
                                                            --inputfile2 CPoutput/out_2014.final.nc4      \
                                                            -c common/USA_adm_all_fips.nc4                \
                                                            -a $crop/aux/$crop.county.nc4                 \
                                                            -m $crop/aux/$crop.mask.0.01.nc4              \
                                                            -n $c                                         \
                                                            -o $finalfile
    src/crop_progress_county/fillGaps.py -i $crop/final/$c.crop_progress.2009-2014.nc4 \
                                         -m $crop/aux/$crop.mask.0.01.nc4              \
                                         -o $finalfile.2
    mv $finalfile.2 $finalfile

    finalfileres=$crop/final/$c.crop_progress.2009-2014.residuals.nc4

    # compute residuals and residual mean and standard deviation
    for v in planting anthesis maturity; do
        ncap2 -O -h -s "${v}_dev=$v-${v}_state" $finalfile $finalfile.tmp
        ncks -O -h -v ${v}_dev $finalfile.tmp $finalfile.tmp
        if [ $v = planting ]; then
            mv $finalfile.tmp $finalfileres
        else
            ncks -h -A $finalfile.tmp $finalfileres
            rm $finalfile.tmp
        fi

        # mean
        ncwa -h -v ${v}_dev -a time $finalfileres $finalfileres.2

        # standard deviation
        ncbo -h -v ${v}_dev $finalfileres $finalfileres.2 $finalfileres.3
        ncra -O -h -y rmssdn $finalfileres.3 $finalfileres.3
        ncwa -O -h -a time $finalfileres.3 $finalfileres.3

        # append
        ncrename -O -h -v ${v}_dev,${v}_dev_mean $finalfileres.2 $finalfileres.2
        ncrename -O -h -v ${v}_dev,${v}_dev_std $finalfileres.3 $finalfileres.3
        ncks -O -h -x -v time $finalfileres.2 $finalfileres.2
        ncks -h -A $finalfileres.2 $finalfileres
        ncks -h -A $finalfileres.3 $finalfileres

        rm $finalfileres.*
    done

    nccopy -d9 -k4 $finalfileres $finalfileres.2
    mv $finalfileres.2 $finalfileres
done