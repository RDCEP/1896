#!/bin/bash

PATH=$PATH:utils

for c in maize soybean sorghum cotton wheat.spring wheat.winter; do
    echo Running $c . . .
    if [ $c = wheat.spring ] || [ $c = wheat.winter ]; then
       crop=wheat
    else
       crop=$c
    fi

    file1=data/$crop/final/$c.crop_progress.nc4 # 1980-2012
    file2=data/$crop/final/$c.crop_progress.2009-2014.nc4 # 2009-2014
    resfile=data/$crop/final/$c.crop_progress.2009-2014.residuals.nc4
    finalfile=data/$crop/final/$c.crop_progress.1980-2014.nc4

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

    # constrain planting date
    if [ $c = sorghum ]; then
python << END
from netCDF4 import Dataset as nc
from numpy.ma import masked_where
f = nc('$finalfile', 'a')
p = f.variables['planting']

pvar = p[:]
pvar[pvar < 60] = 60
pvar[pvar > 195] = 195
p50 = pvar[:, :, :, 2]
p50[p50 < 75] = 75
p50[p50 > 180] = 180
pvar[:, :, :, 2] = p50
pvar = masked_where(p[:].mask, pvar)
p[:] = pvar

f.close()
END
    fi

    if [ $c = wheat.winter ]; then
python << END
from netCDF4 import Dataset as nc
from numpy.ma import masked_where
f = nc('$finalfile', 'a')
p = f.variables['planting']

maxp = [315, 320, 330, 340, 345]

pvar = p[:]
for i in range(len(maxp)):
    pp = p[:, :, :, i]
    pp[pp > maxp[i]] = maxp[i]
    pvar[:, :, :, i] = pp
pvar = masked_where(p[:].mask, pvar)
p[:] = pvar

f.close()
END
    fi

    rm residuals.nc4 crop_progress1.nc4 crop_progress2.nc4
done

# combine wheat
bin/crop_progress/combineWheat.py -s data/wheat/final/wheat.spring.crop_progress.1980-2014.nc4 \
                                  -w data/wheat/final/wheat.winter.crop_progress.1980-2014.nc4 \
                                  -m data/wheat/final/wheat.variety.mask.nc4                   \
                                  -o data/wheat/final/wheat.crop_progress.1980-2014.nc4
