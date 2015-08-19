#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from re import findall
from os.path import isfile
from optparse import OptionParser
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, masked_where
from numpy import ones, zeros, where, resize, array, unique

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--inputfile", dest = "inputfile", default = "maize.reference.county.nc4", type = "string",
                  help = "County-level reference netcdf4 file", metavar = "FILE")
parser.add_option("-a", "--areafile", dest = "areafile", default = "maize.nc4", type = "string",
                  help = "Gridded area file", metavar = "FILE")
parser.add_option("-y", "--yieldfile", dest = "yieldfile", default = None, type = "string",
                  help = "Gridded yield file", metavar = "FILE")
parser.add_option("-c", "--careafile", dest = "careafile", default = "maize.county.nc4", type = "string",
                  help = "County-level area file", metavar = "FILE")
parser.add_option("-f", "--cmapfile", dest = "cmapfile", default = "USA_adm_all_fips.nc4", type = "string",
                  help = "County mapping file", metavar = "FILE")
parser.add_option("-m", "--maskfile", dest = "maskfile", default = "maize.mask.nc4", type = "string",
                  help = "Mask file", metavar = "FILE")
parser.add_option("-o", "--outputfile", dest = "outputfile", default = "maize.reference.nc4", type = "string",
                  help = "Output netcdf4 file", metavar = "FILE")
options, args = parser.parse_args()

inputfile   = options.inputfile
areafile    = options.areafile
yieldfile   = options.yieldfile
careafile   = options.careafile
cmapfile    = options.cmapfile
maskfile    = options.maskfile
outputfile  = options.outputfile

# load county-level reference data
with nc(inputfile) as f:
    time      = f.variables['time'][:]
    tunits    = f.variables['time'].units
    rcounties = f.variables['county'][:]
    irr       = f.variables['irr'].long_name.split(', ')
    ryld      = f.variables['yield'][:]
    rarea     = f.variables['area'][:]

time += int(findall(r'\d+', tunits)[0])

iridx, rfidx, sumidx = [irr.index(i) for i in ['ir', 'rf', 'sum']]

# load area file
with nc(areafile) as f:
    lats, lons = f.variables['lat'][:], f.variables['lon'][:]
    air        = f.variables['irrigated'][:] # hectares
    arf        = f.variables['rainfed'][:]
    asum       = f.variables['sum'][:]

# load yield file
hasyld = not yieldfile is None and isfile(yieldfile)
if hasyld:
    with nc(yieldfile) as f:
        ylats, ylons = f.variables['lat'][:], f.variables['lon'][:]
        ytime        = f.variables['time'][:]
        ytime       += int(findall(r'\d+', f.variables['time'].units)[0])
        yirr         = f.variables['irr'].long_name.split(', ')
        yldfill      = f.variables['yield'][:]

    # select time
    time0, time1   = max(time[0], ytime[0]),      min(time[-1], ytime[-1])
    tidx0, tidx1   = where(time  == time0)[0][0], where(time  == time1)[0][0] + 1
    ytidx0, ytidx1 = where(ytime == time0)[0][0], where(ytime == time1)[0][0] + 1
    yldfill        = yldfill[ytidx0 : ytidx1]

    # get lat/lon map
    latidx, lonidx = where(~yldfill[0, :, :, 0].mask)
    latd    = resize(ylats, (len(ylons), len(ylats))).T
    lond    = resize(ylons, (len(ylats), len(ylons)))
    latd    = latd[latidx, lonidx]
    lond    = lond[latidx, lonidx]
    yldfill = yldfill[:, latidx, lonidx]

    yiridx, yrfidx, ysumidx = [yirr.index(i) for i in ['ir', 'rf', 'sum']]

# load county-level area file
with nc(careafile) as f:
    acounties = f.variables['county'][:]
    cair      = f.variables['irrigated_county'][:]
    carf      = f.variables['rainfed_county'][:]
    casum     = f.variables['sum_county'][:]

# load county map
with nc(cmapfile) as f:
    cmap = f.variables['county'][:]

# mask counties without data
cmapd     = cmap.copy()
ucounties = unique(cmapd)
ucounties = ucounties[~ucounties.mask]
for i in range(len(ucounties)):
    if not ucounties[i] in rcounties:
        cmapd = masked_where(cmapd == ucounties[i], cmapd)
latdc = resize(lats, (len(lons), len(lats))).T
londc = resize(lons, (len(lats), len(lons)))
latdc = latdc[~cmapd.mask]
londc = londc[~cmapd.mask]
cmapd = array(cmapd[~cmapd.mask])

# load mask
with nc(maskfile) as f:
    mlats, mlons = f.variables['lat'][:], f.variables['lon'][:]
    mask = f.variables['mask'][:]

# find unmasked points
latidx, lonidx = where(~mask.mask)

# downscale to grid level
nyears, nlats, nlons, nirr = len(time), len(mlats), len(mlons), len(irr)
sh = (nyears, nlats, nlons, nirr)
yld  = masked_array(zeros(sh), mask = ones(sh))
area = masked_array(zeros(sh), mask = ones(sh))
for i in range(len(latidx)):
    l1, l2 = latidx[i], lonidx[i]

    county = cmap[l1, l2]

    if not county in rcounties:
        # use ray for yield
        if hasyld:
            llidx = ((latd - mlats[l1]) ** 2 + (lond - mlons[l2]) ** 2).argmin()
            yld[tidx0 : tidx1, l1, l2, iridx]  = yldfill[:, llidx, yiridx]
            yld[tidx0 : tidx1, l1, l2, rfidx]  = yldfill[:, llidx, yrfidx]
            yld[tidx0 : tidx1, l1, l2, sumidx] = yldfill[:, llidx, ysumidx]
        else:
            # use nearest county
            llidx = ((latdc - mlats[l1]) ** 2 + (londc - mlons[l2]) ** 2).argmin()
            cidx = where(rcounties == cmapd[llidx])[0][0]
            yld[:, l1, l2, :] = ryld[:, cidx]

        # use mirca for area
        area[:, l1, l2, iridx]  = air[l1,  l2]
        area[:, l1, l2, rfidx]  = arf[l1,  l2]
        area[:, l1, l2, sumidx] = asum[l1, l2]
    else:
        # sample yield
        cidx1 = where(rcounties == county)[0][0]
        yld[:, l1, l2, :] = ryld[:, cidx1]

        # scale area
        cidx2 = where(acounties == county)[0][0]
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
    yearsvar[:] = time - time[0]
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