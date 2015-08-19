#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, masked_where
from numpy import ones, zeros, where, logical_not, unique, resize, array

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.reference.county.nc4", type = "string",
                  help = "County-level reference netcdf4 file", metavar = "FILE")
parser.add_option("-a", "--areafile", dest = "areafile", default = "maize.nc4", type = "string",
                  help = "Gridded area file", metavar = "FILE")
parser.add_option("-c", "--careafile", dest = "careafile", default = "maize.county.nc4", type = "string",
                  help = "County-level area file", metavar = "FILE")
parser.add_option("-f", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-g", "--gapfillfile", dest = "gapfillfile", default = None, type = "string",
                  help = "File that indicates which points to fill with MIRCA (optional)", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile   = options.inputfile
areafile    = options.areafile
careafile   = options.careafile
cmapfile    = options.cmapfile
maskfile    = options.maskfile
gapfillfile = options.gapfillfile
outputfile  = options.outputfile

# load county-level reference data
with nc(inputfile) as f:
    time      = f.variables['time'][:]
    tunits    = f.variables['time'].units
    rcounties = f.variables['county'][:]
    irr       = f.variables['irr'].long_name.split(', ')
    ryld      = f.variables['yield'][:]
    rarea     = f.variables['area'][:]

iridx, rfidx, sumidx = [irr.index(i) for i in ['ir', 'rf', 'sum']]

# load area file
with nc(areafile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    air  = f.variables['irrigated'][:] # hectares
    arf  = f.variables['rainfed'][:]
    asum = f.variables['sum'][:]

# load county-level area file
with nc(careafile) as f:
    acounties = f.variables['county'][:]
    cair      = f.variables['irrigated_county'][:]
    carf      = f.variables['rainfed_county'][:]
    casum     = f.variables['sum_county'][:]

# load county map
with nc(cmapfile) as f:
    cmap = f.variables['county'][:]

# load gap fill file
if gapfillfile:
    with nc(gapfillfile) as f:
        gmask = f.variables['mask'][:]
else:
    gmask = ones((len(lats), len(lons)))

# mask counties without data
cmapd     = cmap.copy()
ucounties = unique(cmapd)
ucounties = ucounties[~ucounties.mask]
for i in range(len(ucounties)):
    if not ucounties[i] in rcounties:
        cmapd = masked_where(cmapd == ucounties[i], cmapd)

# get lat/lon map
latd  = resize(lats, (len(lons), len(lats))).T
lond  = resize(lons, (len(lats), len(lons)))
latd  = latd[~cmapd.mask]
lond  = lond[~cmapd.mask]
cmapd = array(cmapd[~cmapd.mask])

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(logical_not(mask.mask))

# downscale to grid level
nyears, nlats, nlons, nirr = len(time), len(mlats), len(mlons), len(irr)
sh = (nyears, nlats, nlons, nirr)
yld   = masked_array(zeros(sh), mask = ones(sh))
area  = masked_array(zeros(sh), mask = ones(sh))
# darea = masked_array(zeros(sh), mask = ones(sh)) # downscaled area
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    # find county with data
    # totd    = (latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2
    # rcounty = cmapd[totd.argmin()]

    # cidx1 = where(rcounties == rcounty)[0][0]
    # cidx2 = where(acounties == rcounty)[0][0]

    county = cmap[l1, l2]

    if not county in rcounties:
        if gmask[l1, l2]:
            # use straight MIRCA
            area[:, l1, l2, iridx]  = air[l1,  l2]
            area[:, l1, l2, rfidx]  = arf[l1,  l2]
            area[:, l1, l2, sumidx] = asum[l1, l2]
    else:
        cidx1 = where(rcounties == county)[0][0]
        cidx2 = where(acounties == county)[0][0]

        # sample yield
        yld[:,  l1, l2, :] = ryld[:,  cidx1]

        # scale area
        a_x_rf, a_x_ir = arf[l1, l2], air[l1, l2]
        a_c_rf, a_c_ir = carf[cidx2], cair[cidx2]
        for t in range(nyears):
            a_r_rf, a_r_ir = rarea[t, cidx1, rfidx], rarea[t, cidx1, iridx]

            if not a_c_ir and not a_c_rf:
                area[t, l1, l2] = 0
            elif (a_c_rf and a_r_rf / a_c_rf > 20) or (a_c_ir and a_r_ir / a_c_ir > 20):
                ratio = (a_x_rf + a_x_ir) / (a_c_rf + a_c_ir)
                area[t, l1, l2, iridx] = ratio * a_r_ir
                area[t, l1, l2, rfidx] = ratio * a_r_rf
            elif not a_c_ir and a_c_rf:
                area[t, l1, l2, rfidx] = a_x_rf * (a_r_rf / a_c_rf)
                if a_r_rf:
                    area[t, l1, l2, iridx] = area[t, l1, l2, rfidx] * (a_r_ir / a_r_rf)
                else:
                    area[t, l1, l2, iridx] = a_x_rf * (a_r_ir / a_c_rf)
            elif a_c_ir and not a_c_rf:
                area[t, l1, l2, iridx] = a_x_ir * (a_r_ir / a_c_ir)
                if a_r_ir:
                    area[t, l1, l2, rfidx] = area[t, l1, l2, iridx] * (a_r_rf / a_r_ir)
                else:
                    area[t, l1, l2, rfidx] = a_x_ir * (a_r_rf / a_c_ir)
            else:
                area[t, l1, l2, iridx] = a_x_ir * (a_r_ir / a_c_ir)
                area[t, l1, l2, rfidx] = a_x_rf * (a_r_rf / a_c_rf)

            area[t, l1, l2, sumidx] = area[t, l1, l2, iridx] + area[t, l1, l2, rfidx] # sum

with nc(outputfile, 'w') as f:
    f.createDimension('time', nyears)
    yearsvar = f.createVariable('time', 'i4', 'time')
    yearsvar[:] = time
    yearsvar.units = tunits
    yearsvar.long_name = 'time'

    f.createDimension('lat', nlats)
    latvar = f.createVariable('lat', 'f8', 'lat')
    latvar[:] = mlats
    latvar.units = 'degrees_north'
    latvar.long_name = 'latitude'

    f.createDimension('lon', nlons)
    lonvar = f.createVariable('lon', 'f8', 'lon')
    lonvar[:] = mlons
    lonvar.units = 'degrees_east'
    lonvar.long_name = 'longitude'

    f.createDimension('irr', nirr)
    ivar = f.createVariable('irr', 'i4', 'irr')
    ivar[:] = range(1, 1 + nirr)
    ivar.units = 'mapping'
    ivar.long_name = ', '.join(irr)

    yvar = f.createVariable('yield', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    yvar[:] = yld
    yvar.units = 'kg/ha'
    yvar.long_name = 'harvested yield'

    avar = f.createVariable('area', 'f4', ('time', 'lat', 'lon', 'irr'), zlib = True, shuffle = False, complevel = 9, fill_value = 1e20)
    avar[:] = area
    avar.units = 'ha'
    avar.long_name = 'harvested area'