#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import modules
from zipfile import ZipFile
from os.path import split, exists
from os import listdir, sep, mkdir

root   = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014'
outdir = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/nc4.2009-2013'

infiles  = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/bin/dbf2nc/in_files.txt'
outfiles = '/project/joshuaelliott/data/nass.crop-progress.county.2009-2014/bin/dbf2nc/out_files.txt'

fin  = open(infiles, 'w')
fout = open(outfiles, 'w')

# 2009-2011
for drct in ['CP_data_files-2009', 'CP_data_files-2010', 'CP_data_files-2011']:
    dirnames = [l for l in listdir(root + sep + drct) if not l.startswith('.')]

    for i in range(len(dirnames)):
        yyyydddd = dirnames[i][2 :]
        yyyydddd = '20' + yyyydddd[-2 :] + yyyydddd[: 4]

        d = root + sep + drct + sep + dirnames[i]
        zfile = [z for z in listdir(d) if z.lower().endswith('.zip')]

        if len(zfile) == 1:
            zfile = d + sep + zfile[0]
            zobj  = ZipFile(zfile) # unzip file

            d2 = d + sep + 'temp'
            if not exists(d2):
                mkdir(d2) # temporary directory to save files
                for name in zobj.namelist():
                    dirname, filename = split(name)
                    if filename.endswith('.DBF') and not filename.endswith('99.DBF'):
                        f = open(d2 + sep + name, 'w')
                        f.write(zobj.read(name))
                        f.close()

            for f in listdir(d2):
                fin.write('%s/%s\n' % (d2, f))
                fout.write('%s/out_%s_%s.nc4\n' % (outdir, yyyydddd, f.strip('.DBF')))

# 2012-2013
for drct in ['CP_data_files-2012', 'CP_data_files-2013']:
    dirnames = [l for l in listdir(root + sep + drct) if not l.startswith('.')]

    for i in range(len(dirnames)):
        d = root + sep + drct + sep + dirnames[i]
        filenames = [f for f in listdir(d) if f.endswith('.DBF')]

        for fn in filenames:
            fin.write('%s/%s\n' % (d, fn))
            fout.write('%s/out_%s_%s.nc4\n' % (outdir, dirnames[i], fn.strip('.DBF')))

fin.close()
fout.close()