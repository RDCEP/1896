#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from zipfile import ZipFile
from os.path import split, exists
from os import listdir, sep, mkdir

indir  = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/CP_data_files-2014'
outdir = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/nc4.2014'

infiles  = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/bin/csv2nc/in_files.txt'
outfiles = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/bin/csv2nc/out_files.txt'

fin  = open(infiles, 'w')
fout = open(outfiles, 'w')

# csv archive
drct = '2014archive'
files = [f for f in listdir(indir + sep + drct) if f.endswith('.csv')]
for i in range(len(files)):
    state, date = files[i].strip('.csv').split('_')

    yyyydddd = date[-4 :] + date[: 4]

    fin.write(indir + sep + drct + sep + files[i] + '\n')
    fout.write(outdir + sep + 'out_' + yyyydddd + '_' + state + '.nc4\n')

# zip files
files = [f for f in listdir(indir) if f.endswith('.zip')]
for i in range(len(files)):
    date = files[i].strip('.zip')

    yyyydddd = date[-4 :] + date[: 4]

    zobj = ZipFile(indir + sep + files[i]) # unzip file

    drct = indir + sep + date
    if not exists(drct):
        mkdir(drct) # temporary directory to save files
    for name in zobj.namelist():
        dirname, filename = split(name)
        if filename.endswith('.csv'):
            f = open(drct + sep + name, 'w')
            f.write(zobj.read(name))
            f.close()
            fin.write('%s/%s\n' % (drct, name))
            fout.write('%s/out_%s_%s.nc4\n' % (outdir, yyyydddd, name.strip('.csv')))

fin.close()
fout.close()