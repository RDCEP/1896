from csv import reader
from calendar import isleap
from datetime import datetime
from numpy.ma import masked_array
from scipy.optimize import curve_fit
from numpy import double, zeros, ones, unique, logical_and, exp, log, array, interp, where, logical_not

class StateDistances(object):
    def __init__(self, sdfile):
        data = []
        with open(sdfile, 'rU') as f:
            for row in reader(f):
                data.append(row)

        self.code = [int(c) for c in data[1][2 :]]

        nstates = len(self.code)

        self.dist = zeros((nstates, nstates))
        for i in range(nstates):
            self.dist[i] = [double(d.replace(',', '')) for d in data[i + 2][2 :]]

    def closestState(self, fromState, toStates):
        fromIdx = self.code.index(fromState)
        dists   = [self.dist[fromIdx, self.code.index(i)] for i in toStates]
        return toStates[array(dists).argmin()]

class CropProgressData(object):
    def __init__(self, cpfile, sdfile, var):
        data = []
        with open(cpfile, 'rU') as f:
            for row in reader(f):
                data.append(row)

        header = data[0]

        week_idx  = header.index('Week Ending')
        state_idx = header.index('State ANSI')
        var_idx   = header.index('Data Item')
        value_idx = header.index('Value')

        if var == 'maize':
            planting_label = 'CORN - PROGRESS, MEASURED IN PCT PLANTED'
            anthesis_label = 'CORN - PROGRESS, MEASURED IN PCT SILKING'
            maturity_label = 'CORN - PROGRESS, MEASURED IN PCT MATURE'
        elif var == 'soybean':
            planting_label = 'SOYBEANS - PROGRESS, MEASURED IN PCT PLANTED'
            anthesis_label = 'SOYBEANS - PROGRESS, MEASURED IN PCT BLOOMING'
            maturity_label = 'SOYBEANS - PROGRESS, MEASURED IN PCT DROPPING LEAVES'
        elif var == 'sorghum': 
            planting_label = 'SORGHUM - PROGRESS, MEASURED IN PCT PLANTED'
            anthesis_label = 'SORGHUM - PROGRESS, MEASURED IN PCT HEADED'
            maturity_label = 'SORGHUM - PROGRESS, MEASURED IN PCT MATURE'
        elif var == 'cotton':
            planting_label = 'COTTON, UPLAND - PROGRESS, MEASURED IN PCT PLANTED'
            anthesis_label = 'COTTON, UPLAND - PROGRESS, MEASURED IN PCT SETTING BOLLS'
            maturity_label = 'COTTON, UPLAND - PROGRESS, MEASURED IN PCT BOLLS OPENING'
        else:
            raise Exception('Unknown crop')

        nd = len(data) - 1

        self.year  = zeros(nd, dtype = int)
        self.day   = zeros(nd, dtype = int)
        self.state = zeros(nd, dtype = int)
        self.var   = zeros(nd, dtype = '|S32')
        self.value = zeros(nd)
        for i in range(nd):
            line = data[i + 1]

            year, month, day = [int(j) for j in line[week_idx].split('-')]
            jday = int(datetime(year, month, day).strftime('%j')) - 3

            self.state[i] = int(line[state_idx])

            data_item = line[var_idx]
            if data_item == planting_label:
                self.var[i] = 'planting'
            elif data_item == anthesis_label:
                self.var[i] = 'anthesis'
            elif data_item == maturity_label:
                self.var[i] = 'maturity'
            else:
                self.var[i] = 'other'

            if var == 'cotton' and self.var[i] == 'maturity':
                # cotton's maturity is a week after bolls opening
                jday += 7

            if jday < 1:
                year -= 1
                jday = 365 + isleap(year) - jday
            elif jday > 365 + isleap(year):
                jday -= 365 + isleap(year)
            self.year[i] = year
            self.day[i]  = jday

            self.value[i] = double(line[value_idx])

        self.years  = unique(self.year)
        self.states = unique(self.state)
        self.per    = array([10, 25, 50, 75, 90]) # percentiles

        self.sd = StateDistances(sdfile) # state distances

    def getVar(self, varname):
        nyears, nstates, nper = len(self.years), len(self.states), len(self.per)

        var = masked_array(zeros((nyears, nstates, nper)), mask = ones((nyears, nstates, nper)))

        is_var = self.var == varname
        for i in range(nyears):
            is_year = self.year == self.years[i]
            is_var_year = logical_and(is_var, is_year)
            for j in range(nstates):
                is_state = self.state == self.states[j]
                is_var_year_state = logical_and(is_var_year, is_state)
                if is_var_year_state.sum():
                    days = array(self.day[is_var_year_state])
                    values = array(self.value[is_var_year_state])
                    var[i, j] = self.__interpolate(days, values, self.per)

        # fill in missing years with same years from neighboring state
        for i in range(nstates):
            idx = where(var[:, i, :].mask.all(axis = 1))[0]
            if not idx.size: continue

            for j in idx:
                idx2 = where(logical_not(var[j, :, :].mask.all(axis = 1)))[0]
                if not idx2.size: continue

                cstate = self.sd.closestState(self.states[i], self.states[idx2])
                sidx = where(self.states == cstate)[0][0]
                var[j, i, :] = var[j, sidx, :]

        # fill in remaining years with yearly averages
        for i in range(nstates):
            for j in range(nper):
                v = var[:, i, j]
                v[v.mask] = v.mean()
                var[:, i, j] = v.copy()

        return var

    def __interpolate(self, xp, yp, y):
        span = 42 # 6 weeks

        ymin, ymax = y.min(), y.max()
        ypmin, ypmax = yp.min(), yp.max()

        if ypmin <= ymin and ypmax >= ymax:
            # interpolation
            x = interp(y, yp, xp)
        elif len(xp) == 1 or ypmax - ypmin <= 2:
            # line-fit
            slope = 80. / span
            intercept = yp[0] - slope * xp[0]
            x = self.__inverse_line(y, slope, intercept)
        else:
            # extrapolation
            try:
                x = self.__fit_sigmoid(xp, yp, y)
                if any(x > 400):
                    x = self.__fit_line(xp, yp, y)
            except:
                x = self.__fit_line(xp, yp, y)

        return x

    def __sigmoid(self, x, x0, k):
        return 1 / (1 + exp(-k * (x - x0)))
    def __inverse_sigmoid(self, y, x0, k):
        return x0 - log(1 / y - 1) / k
    def __fit_sigmoid(self, xp, yp, y):
        xpscale = xp / 100.
        ypscale = yp / 100.
        popt = curve_fit(self.__sigmoid, xpscale, ypscale)[0]
        return self.__inverse_sigmoid(y / 100., *popt) * 100.

    def __line(self, x, m, b):
        return m * x + b
    def __inverse_line(self, y, m, b):
        return (y - b) / m
    def __fit_line(self, xp, yp, y):
        popt = curve_fit(self.__line, xp, yp)[0]
        return self.__inverse_line(y, *popt)