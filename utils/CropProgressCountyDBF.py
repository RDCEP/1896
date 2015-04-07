from dbfpy.dbf import Dbf as dbf
from numpy.ma import masked_array
from numpy import zeros, ones, unique, where, sqrt, pi, exp, logical_and

class CropProgressDataDBF(object):
    dthr = 1000. # distance threshold for nearest neighbor (km)
    dstd = 40.   # gaussian kernel standard deviation (km)

    w0 = 1 / dstd / sqrt(2 * pi) # central weight in smoothing

    def __init__(self, cpfile, cdobj): # cdobj = crop distance object
        db = dbf(cpfile)

        nd = len(db)

        self.day     = zeros(nd, dtype = int)
        self.state   = zeros(nd, dtype = int)
        self.county  = zeros(nd, dtype = int)
        self.var     = zeros(nd, dtype = int)
        self.value   = zeros((2, nd))
        self.nreport = zeros((2, nd), dtype = int)

        for i in range(nd):
            try:
                self.day[i]        = int(db[i]['DWEEK'].strftime('%Y%j'))
                self.state[i]      = db[i]['NSTATE']
                self.county[i]     = db[i]['NCNTY']
                self.var[i]        = db[i]['NCODE']
                self.value[0, i]   = db[i]['NDATA']
                self.value[1, i]   = db[i]['NADATA']
                self.nreport[0, i] = db[i]['NREPORT']
                self.nreport[1, i] = db[i]['NIMPUTE'] + self.nreport[0, i] # add reports
            except:
                self.day[i] = -1 # invalid data

        isvalid = logical_and(self.day != -1, self.county != 999) # remove bad data and district aggregates

        self.day     = self.day[isvalid]
        self.state   = self.state[isvalid]
        self.county  = self.county[isvalid]
        self.var     = self.var[isvalid]
        self.value   = self.value[:, isvalid]
        self.nreport = self.nreport[:, isvalid]

        self.usc = self.state * 1000 + self.county # unique state-county

        self.day      = self.day[0] if len(self.day) else [] # single day
        self.counties = unique(self.usc)
        self.vars     = unique(self.var)

        self.cd = cdobj

    def getVar(self, varname):
        ndtype, ncounties = len(self.value), len(self.counties)

        var = masked_array(zeros((ndtype, ncounties)), mask = ones((ndtype, ncounties)))

        is_var = self.var == varname

        for i in range(ncounties):
            is_county = self.usc == self.counties[i]
            is_var_county = logical_and(is_var, is_county)
            is_var_not_county = logical_and(is_var, ~is_county)

            if not is_var_county.sum(): # county not found
                continue

            values   = self.value[:, is_var_county].squeeze()
            nreports = self.nreport[:, is_var_county].squeeze()

            var[nreports >= 3, i] = values[nreports >= 3]

            for j in where(logical_and(nreports > 0, nreports < 3))[0]:
                # neighboring counties with data
                is_valid  = logical_and(is_var_not_county, self.value[j] != -1)
                ncounties = unique(self.usc[is_valid])

                # closest counties with data
                ccounties, cdistances = self.cd.closestCounty(self.counties[i], ncounties, self.dthr)

                nneighbors = 3 - nreports[j]
                if len(ccounties) < nneighbors:
                    continue

                var[j, i] = self.w0 * values[j]
                weights   = self.w0

                for n in range(nneighbors):
                    is_ccounty = self.usc == ccounties[n]
                    cvalue     = self.value[j, logical_and(is_var, is_ccounty)].squeeze()
                    cweight    = exp(-0.5 * (cdistances[n] / self.dstd) ** 2) / self.dstd / sqrt(2 * pi)
                    var[j, i] += cvalue * cweight
                    weights   += cweight
                var[j, i] /= weights

        return var