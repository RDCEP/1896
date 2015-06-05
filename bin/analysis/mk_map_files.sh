#!/bin/bash

futdir=/project/joshuaelliott/psims/outputs/1896/future
histdir=/project/joshuaelliott/psims/outputs/1896/calibration
outdir=/project/joshuaelliott/1896/bin/analysis

wdir=/project/joshuaelliott/psims/data/masks/weights/1896

for c in mai cot soy; do
   if [ $c = mai ]; then
      wfile=$wdir/maize.NA.nc4
   elif [ $c = cot ]; then
      wfile=$wdir/cotton.NA.nc4
   else
      wfile=$wdir/soybean.NA.nc4
   fi

   # process variables
   for s in hadgem_85_adapt_nop hadgem_85_dev_nop no_clim_85 hist; do
      for v in HWAM IRCM ETCP; do
         if [ $s = hist ]; then
            # historical
            file=$(ls $histdir/$c/hist-all/*${v}.nc4)
            cp $file tmp.nc4
         else
            # future
            if [ $s = hadgem_85_adapt_nop ]; then
               s2=hadgem.85.adapt.nop
            elif [ $s = hadgem_85_dev_nop ]; then
               s2=hadgem.85.dev.nop
            else
               s2=no-clim.85
            fi
            file=$(ls $futdir/$c/slope/${s2}/*${v}.nc4)
            ncks -h -d time,30,39 $file tmp.nc4 # select 2040s
         fi
         ncwa -O -h -a time tmp.nc4 tmp.nc4
         ncks -O -h -x -v time tmp.nc4 tmp.nc4
         ncwa -O -h -a scen tmp.nc4 tmp.nc4
         ncks -O -h -x -v scen tmp.nc4 tmp.nc4
         ncrename -O -h -v $v,${v}_${s} tmp.nc4 tmp.nc4

         # add weights
         ncks -h -A $wfile tmp.nc4

         # compute sum
         comm1=$(echo "${v}_${s}_sum=(${v}_${s}(:,:,0)*irrigated+${v}_${s}(:,:,1)*rainfed)/sum")
         comm2=$(echo "where(sum==0) ${v}_${s}_sum=1e20")
         ncap2 -O -h -s "$comm1" tmp.nc4 tmp.nc4
         ncap2 -O -h -s "$comm2" tmp.nc4 tmp.nc4
         ncks -O -h -x -v irrigated,rainfed,sum tmp.nc4 tmp.nc4

         if [ $v = HWAM ]; then
            mv tmp.nc4 $s.nc4
         else
            ncks -h -A tmp.nc4 $s.nc4
            rm tmp.nc4
         fi
      done

      if [ $s = hadgem_85_adapt_nop ]; then
         mv $s.nc4 $c.nc4
      else
         ncks -h -A $s.nc4 $c.nc4
         rm $s.nc4
      fi
   done

   # compute new variables
   for s in hadgem_85_adapt_nop hadgem_85_dev_nop no_clim_85; do
      comm1=$(echo "HWAMdETCP_${s}_sum=HWAM_${s}_sum/ETCP_${s}_sum")
      comm2=$(echo "where(ETCP_${s}_sum==0) HWAMdETCP_${s}_sum=1e20")
      ncap2 -O -h -s "$comm1" $c.nc4 $c.nc4
      ncap2 -O -h -s "$comm2" $c.nc4 $c.nc4

      comm1=$(echo "irrValue_${s}=(HWAM_${s}(:,:,0)-HWAM_${s}(:,:,1))/IRCM_${s}_sum")
      comm2=$(echo "where(IRCM_${s}_sum==0) irrValue_${s}=1e20")
      ncap2 -O -h -s "$comm1" $c.nc4 $c.nc4
      ncap2 -O -h -s "$comm2" $c.nc4 $c.nc4

      comm1=$(echo "IRCM_pd_${s}_hist=100*(IRCM_${s}_sum-IRCM_hist_sum)/IRCM_hist_sum")
      comm2=$(echo "where(IRCM_hist_sum==0) IRCM_pd_${s}_hist=1e20")
      ncap2 -O -h -s "$comm1" $c.nc4 $c.nc4
      ncap2 -O -h -s "$comm2" $c.nc4 $c.nc4
   done

   # compute percent differences
   for v in HWAM IRCM ETCP HWAMdETCP; do
      comm1=$(echo "${v}_pd=100*(${v}_hadgem_85_adapt_nop_sum-${v}_no_clim_85_sum)/${v}_no_clim_85_sum")
      comm2=$(echo "where(${v}_no_clim_85_sum==0) ${v}_pd=1e20")
      ncap2 -O -h -s "$comm1" $c.nc4 $c.nc4
      ncap2 -O -h -s "$comm2" $c.nc4 $c.nc4
   done

   # remove variables
   for s in hadgem_85_adapt_nop hadgem_85_dev_nop no_clim_85 hist; do
      for v in HWAM IRCM ETCP; do
         ncks -O -h -x -v ${v}_${s},${v}_${s}_sum $c.nc4 $c.nc4
      done
      if [ $s != hist ]; then
         ncks -O -h -x -v HWAMdETCP_${s}_sum $c.nc4 $c.nc4
      fi
   done
   ncks -O -h -x -v irr $c.nc4 $c.nc4

   nccopy -d9 -k4 $c.nc4 $c.nc4.2
   mv $c.nc4.2 $c.nc4
done
