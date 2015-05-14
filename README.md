# 1896
Various utilities and codes developed for pSIMS applications around the 1896 project

UTILITIES
=========

Several postprocessing Python utilities are available in the repository. These include the following.

   bin/campaign/convert2date.py -i \<inputfile\> -v \<variable\> -o \<outputfile\>

This script converts a date variable given by \<variable\> in \<inputfile\> from a Julian day representation to a YYYYMMDD representation. The new date variable is stored as an integer in \<outputfile\>.

   bin/campaign/extrapolateGrid.py -i \<inputfile\> -m \<maskfile\> -v \<variable\> --wlat \<wlat\> --wlon \<wlon\> -o \<outputfile\>

This script extrapolates \<variable\> from \<inputfile\> to all points in \<maskfile\> and saves the result to \<outputfile\>. The distance measure used for extrapolation is a weighted Euclidean distance in latitude-longitude space, where \<wlat\> and \<wlon\> are the latitude and longitude weights, respectively. Both weights default to one.

   bin/campaign/filterGrid.py -i \<inputfile\> -v \<variable\> -m \<minval\> -o \<outputfile\>

This script sets \<variable\> to its median value for points whose deviation from the median is greater than 1.5 times the standard deviation or \<minval\>, whichever is greater. The result is saved into \<outputfile\>.

   bin/campaign/maskunion.py --inputfile1 \<inputfile1\> --inputfile2 \<inputfile2\> -o \<outputfile\>

This script returns the mask union of two mask netCDF files \<inputfile1\> and \<inputfile2\> and saves the result to \<outputfile\>. The masks of the input files are designated by the "mask" variable.

   bin/campaign/nc2gridlist.py -i \<inputfile\> -o \<outputfile\>

This script converts a mask netCDF file \<inputfile\> to its corresponding gridlist \<outputfile\>.

   bin/campaign/cropprogress2campaign.planting.py -i \<inputfile\> -m \<maskfile\> --wlat \<wlat\> --wlon \<wlon\> -o \<outputfile\>

This script takes the 50th percentile planting date from \<inputfile\>, extrapolates it to the mask given in \<maskfile\> using the weights \<wlat\> and \<wlon\>, converts it to the YYYYMMDD representation, and saves the result in \<outputfile\>.
