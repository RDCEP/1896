#!/bin/bash

PATH=$PATH:/project/joshuaelliott/psims/utils

indir=/project/joshuaelliott/1896/data

maskfile=$indir/common/USA_CAN_adm_all_fips.nc4

for c in wheat.winter wheat.spring maize soybean sorghum cotton; do
   echo Running $c . . .
   if [ $c = wheat.winter ] || [ $c = wheat.spring ]; then
      crop=wheat
   else
      crop=$c
   fi

   # aggregate crop progress
   cpaggfile=$indir/$crop/final/$c.crop_progress.1980-2014.agg.nc4
   ncrename -h -v per,scen $indir/$crop/final/$c.crop_progress.1980-2014.nc4 crop_progress.nc4
   ncrename -h -v sum,weights $indir/$crop/aux/$c.NA.nc4 weights.nc4
   /project/joshuaelliott/psims/bin/agg.out.noirr.py -i crop_progress.nc4:planting,anthesis,maturity -w weights.nc4 -a $maskfile -n 10 -l time -o $cpaggfile
   ncrename -O -h -v scen,per $cpaggfile $cpaggfile
   rm crop_progress.nc4

   # aggregate yield reference
   aggfile=$indir/$crop/final/$c.reference.agg.nc4
   aggareafile=$indir/$crop/final/$c.reference.agg.area.nc4
   ncks -h -d irr,0,1 $indir/$crop/final/$c.reference.nc4 reference.nc4
   ncatted -O -h -a long_name,irr,m,c,"ir, rf" reference.nc4 reference.nc4
   /project/joshuaelliott/psims/bin/agg.out.py -i reference.nc4:yield -w weights.nc4 -a $maskfile -n 10 -l time -o $aggfile # yield
   /project/joshuaelliott/psims/bin/agg.out.py -i reference.nc4:area -t sum -a $maskfile -n 10 -l time -o $aggareafile # area
   ncks -h -A $aggareafile $aggfile
   rm weights.nc4 reference.nc4 $aggareafile
done
