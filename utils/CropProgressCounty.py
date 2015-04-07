from csv import reader
from datetime import datetime
from numpy.ma import masked_array
from numpy import double, zeros, ones, unique, sqrt, pi, exp, logical_and

class CropProgressData(object):
    dthr = 1000. # distance threshold for nearest neighbor (km)
    dstd = 40.   # gaussian kernel standard deviation (km)

    w0 = 1 / dstd / sqrt(2 * pi) # central weight in smoothing

    def __init__(self, cpfile, cdobj): # cdobj = crop distance object
        data = []
        with open(cpfile, 'rU') as f:
            for row in reader(f):
                data.append(row)

        week_idx   = 0
        state_idx  = 1
        county_idx = 2
        var_idx    = 3
        value_idx  = 4

        nd = len(data)

        self.day    = zeros(nd, dtype = int)
        self.state  = zeros(nd, dtype = int)
        self.county = zeros(nd, dtype = int)
        self.var    = zeros(nd, dtype = '|S32')
        self.value  = zeros(nd)
        for i in range(nd):
            line = data[i]

            month, day, year = [int(j) for j in line[week_idx].split('/')]

            self.day[i]    = int(datetime(year, month, day).strftime('%Y%j'))
            self.state[i]  = int(line[state_idx])
            self.county[i] = int(line[county_idx])
            self.var[i]    = line[var_idx]
            self.value[i]  = double(line[value_idx])

        isvalid = self.value != -1 # remove NULLs (-1s)

        self.day    = self.day[isvalid]
        self.state  = self.state[isvalid]
        self.county = self.county[isvalid]
        self.var    = self.var[isvalid]
        self.value  = self.value[isvalid]

        self.usc = self.state * 1000 + self.county # unique state-county

        self.day      = self.day[0] # single day
        self.counties = unique(self.usc)
        self.vars     = unique(self.var)

        self.cd = cdobj

    def getVar(self, varname):
        ncounties = len(self.counties)

        var = masked_array(zeros(ncounties), mask = ones(ncounties))

        is_var = self.var == varname

        for i in range(ncounties):
            is_county = self.usc == self.counties[i]
            is_var_county = logical_and(is_var, is_county)

            if not is_var_county.sum(): # county not found
                continue

            values = self.value[is_var_county]

            if len(values) >= 3: # at least three points
                var[i] = values.mean()
                continue

            # neighboring counties with data
            is_var_not_county = logical_and(is_var, ~is_county)
            ncounties = unique(self.usc[is_var_not_county])

            # closest counties with data
            ccounties, cdistances = self.cd.closestCounty(self.counties[i], ncounties, self.dthr)

            nneighbors = 3 - len(values)
            if len(ccounties) < nneighbors:
                continue

            var[i]  = (self.w0 * values).sum()
            weights = len(values) * self.w0

            for n in range(nneighbors):
                is_ccounty = self.usc == ccounties[n]
                cvalue     = self.value[logical_and(is_var, is_ccounty)].mean()
                cweight    = exp(-0.5 * (cdistances[n] / self.dstd) ** 2) / self.dstd / sqrt(2 * pi)
                var[i]    += cvalue * cweight
                weights   += cweight
            var[i] /= weights

        return var