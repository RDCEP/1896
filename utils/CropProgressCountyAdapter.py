import abc
from netCDF4 import Dataset as nc
from numpy.ma import masked_array, isMaskedArray, masked_where
from numpy import array, zeros, ones, where, interp, append, union1d, unique, diff

class StateAggregator(object):
    def __init__(self, smapfile, areafile):
        with nc(smapfile) as f:
            self.smap = f.variables['state'][:]
            self.cmap = f.variables['county'][:]
        self.states = unique(self.smap)
        self.states = self.states[~self.states.mask]

        with nc(areafile) as f:
            self.acounties = f.variables['county'][:]
            self.area      = f.variables['sum_county'][:]

    def aggregate(self, cdata, counties):
        nyears, nweeks, ncounties, nvars = cdata.shape

        nstates = len(self.states)

        sdata = masked_array(zeros((nyears, nweeks, nstates, nvars)), mask = ones((nyears, nweeks, nstates, nvars)))
        for i in range(nstates):
            cts = unique(self.cmap[self.smap == self.states[i]])
            cts = cts[~cts.mask]

            cidx1 = []
            cidx2 = []
            for j in range(len(cts)):
                if cts[j] in counties and cts[j] in self.acounties:
                    cidx1.append(where(counties == cts[j])[0][0])
                    cidx2.append(where(self.acounties == cts[j])[0][0])

            if len(cidx1):
                data = self.__harmonizeCounties(cdata[:, :, cidx1])

                tarea = zeros(data.shape)
                for j in range(len(cidx2)):
                    tarea[:, :, j] = self.area[cidx2[j]]
                tarea = masked_where(data.mask, tarea)

                sdata[:, :, i] = (data * tarea).sum(axis = 2) / tarea.sum(axis = 2)

        return sdata

    def __harmonizeCounties(self, data):
        data2 = data.copy()

        nyears, nweeks, ncounties, nvars = data.shape

        for i in range(nyears):
            for j in range(nvars):
                d = data[i, :, :, j] # week x county

                idx = where(~d.mask.all(axis = 1))[0]

                for k in range(ncounties):
                    dc = d[idx, k]

                    if isMaskedArray(dc) and dc.mask.any() and not dc.mask.all():
                        # fill left and right with 0 and 100, respectively
                        idx2 = where(~dc.mask)[0]
                        dc[: idx2[0]] = 0.
                        dc[idx2[-1] + 1 :] = 100.

                        # interpolate
                        x = where(~dc.mask)[0]
                        y = dc[~dc.mask]
                        dc = interp(range(len(idx)), x, y)

                    data2[i, idx, k, j] = dc

        return data2

class CropProgressCountyAdapterBase(object):
    @abc.abstractmethod
    def getCountyVar(self, var): return

    @abc.abstractmethod
    def getStateVar(self, var):  return

    def getVar(self, data, var, varlist, years, per, crop):
        if not var in varlist:
            raise Exception('%s unavailable' % var)

        nregions = data.shape[2]

        nyears, nper = len(years), len(per)

        varr = masked_array(zeros((nyears, nregions, nper)), mask = ones((nyears, nregions, nper)))

        varidx = varlist.index(var)

        for i in range(nyears):
            for j in range(nregions):
                varr[i, j] = self.__interpolate(self.per, data[i, :, j, varidx], self.day[i])

        if crop in ['wheat.winter', 'wheat.spring'] and var == 'anthesis':
            varr += 4
        elif crop in ['wheat.winter', 'wheat.spring'] and var == 'maturity':
            varr -= 10
        elif crop in ['barley', 'rapeseed'] and var == 'maturity':
            varr -= 7
        elif crop == 'cotton' and var == 'maturity':
            varr += 7

        return varr

    def __interpolate(self, xi, x, y):
        if isMaskedArray(x):
            if x.mask.all():
                return masked_array(zeros(len(xi)), mask = ones(len(xi)))
            else:
                y = y[~x.mask]
                x = x[~x.mask]
        dx = where(diff(x) < -10)[0]
        if dx.size:
            x = x[: dx[0] + 1]
            y = y[: dx[0] + 1]
        return interp(xi, x, y)

class CropProgressCountyAdapterComposite(CropProgressCountyAdapterBase):
    def __init__(self, cpfile1, cpfile2, smapfile, areafile, crop):
        self.cp1 = CropProgressCountyAdapter(cpfile1, smapfile, areafile, crop, 'nadata')
        self.cp2 = CropProgressCountyAdapter(cpfile2, smapfile, areafile, crop, 'data')

        self.year   = append(self.cp1.year, self.cp2.year)
        self.county = union1d(self.cp1.county, self.cp2.county)
        self.state  = union1d(self.cp1.state, self.cp1.state)
        self.per    = self.cp1.per

        if crop == 'wheat.winter':
            self.year = append(self.year - 1, self.year[-1])

        self.crop = crop

    def getCountyVar(self, var):
        nyears, ncounties, nper = len(self.year), len(self.county), len(self.per)

        nyears1, nyears2 = len(self.cp1.year), len(self.cp2.year)

        v1 = self.cp1.getCountyVar(var)
        v2 = self.cp2.getCountyVar(var)

        # harmonize along county
        varr = masked_array(zeros((nyears1 + nyears2, ncounties, nper)), mask = ones((nyears1 + nyears2, ncounties, nper)))
        for i in range(ncounties):
            c = self.county[i]
            if c in self.cp1.county:
                idx = where(self.cp1.county == c)[0][0]
                varr[: nyears1, i] = v1[:, idx]
            if c in self.cp2.county:
                idx = where(self.cp2.county == c)[0][0]
                varr[nyears1 :, i] = v2[:, idx]

        if self.crop == 'wheat.winter':
            newvarr = masked_array(zeros((nyears, ncounties, nper)), mask = ones((nyears, ncounties, nper)))
            newvarr[: nyears1 + nyears2] = varr
            varr = newvarr

        return varr

    def getStateVar(self, var):
        nyears1, nyears2 = len(self.cp1.year), len(self.cp2.year)

        v1 = self.cp1.getStateVar(var)
        v2 = self.cp2.getStateVar(var)

        sh = array(v1.shape)
        sh[0] = nyears1 + nyears2
        varr = masked_array(zeros(sh), mask = ones(sh))

        varr[: nyears1] = v1
        varr[nyears1 :] = v2

        if self.crop == 'wheat.winter':
            sh[0] = len(self.year)
            newvarr = masked_array(zeros(sh), mask = ones(sh))
            newvarr[: nyears1 + nyears2] = varr
            varr = newvarr

        return varr

class CropProgressCountyAdapter(CropProgressCountyAdapterBase):
    vars = ['planting', 'anthesis', 'maturity', 'emergence']

    varmap_num = {'maize':        [105, 106, 109, 111], \
                  'soybean':      [135, 136, 138, ''],  \
                  'sorghum':      [195, 196, 198, ''],  \
                  'cotton':       [165, 167, 168, ''],  \
                  'wheat.winter': [255, 257, 258, ''],  \
                  'wheat.spring': [285, 287, 288, ''],  \
                  'barley':       [[335, 505, 606, 700, 460, 345], [337, 507, 610, 708, 462, 349], [338, 509, 612, 701, 463, 352], ''], \
                  'rapeseed':     [[166, 460, 826, 855], [462, 828, 858], [861, 464, 830], '']}

    varmap_str = {'maize':        ['CCRNPLPG', 'CCRNSIPG', 'CCRNMAPG', 'CCRNEMPG'], \
                  'soybean':      ['CSOYPLPG', 'CSOYBLPG', 'CSOYDLPG', ''],         \
                  'sorghum':      ['CSRGPLPG', 'CSRGHEPG', 'CSRGMAPG', ''],         \
                  'cotton':       ['CCTUPLPG', 'CCTUSBPG', 'CCTUBOPG', ''],         \
                  'wheat.winter': ['CWWHPLPG', 'CWWHHEPG', 'CWWHHVPG', ''],         \
                  'wheat.spring': ['CSWHPLPG', 'CSWHHEPG', 'CSWHHVPG', ''],         \
                  'barley':       ['CBARPLPG', 'CBARHEPG', 'CBARHVPG', ''],         \
                  'rapeseed':     ['CCANPLPG', 'CCANBLPG', 'CCANHVPG', '']}

    per = array([10, 25, 50, 75, 90]) # percentiles

    def __init__(self, cpfile, smapfile, areafile, crop, varname):
        with nc(cpfile) as f:
            self.year    = f.variables['year'][:]
            self.week    = f.variables['week'][:]
            self.county  = f.variables['county'][:]
            self.day     = f.variables['day'][:]
            self.rawdata = f.variables[varname][:]

            varatt = f.variables['var'].ncattrs()
            if 'units' in varatt and f.variables['var'].units == 'mapping':
                self.var = array(f.variables['var'].long_name.split(', '))
                self.varmap = self.varmap_str[crop]
            else:          
                self.var = f.variables['var'][:]
                self.varmap = self.varmap_num[crop]

        self.crop = crop

        nyears, nweeks, ncounties, nvars = len(self.year), len(self.week), len(self.county), len(self.vars)

        self.data = masked_array(zeros((nyears, nweeks, ncounties, nvars)), mask = ones((nyears, nweeks, ncounties, nvars)))
        for i in range(nvars):
            vmap = self.varmap[i]

            if isinstance(vmap, list):
                for j in range(ncounties):
                    for k in range(len(vmap)):
                        if vmap[k] in self.var: # variable in list
                            varidx = where(self.var == vmap[k])[0][0]
                            data   = self.rawdata[:, :, varidx, j]
                            if not isMaskedArray(data) or not data.mask.all():
                                self.data[:, :, j, i] = data
                                break
            elif vmap != '':
                if vmap in self.var:
                    varidx = where(self.var == vmap)[0][0]
                    self.data[:, :, :, i] = self.rawdata[:, :, varidx, :]
            else: # no data
                continue

            # discard counties with insufficient data
            for j in range(ncounties):
                for k in range(nyears):
                    data = self.data[k, :, j, i]

                    if isMaskedArray(data):
                        data = data[~data.mask]

                    if data.size and data[-1] - data[0] < 40:
                        self.data[k, :, j, i].mask = True # mask

        # aggregate to state level
        aggregator = StateAggregator(smapfile, areafile)
        self.sdata = aggregator.aggregate(self.data, self.county)
        self.state = aggregator.states

    def getCountyVar(self, var): return self.getVar(self.data,  var, self.vars, self.year, self.per, self.crop)
    def getStateVar(self,  var): return self.getVar(self.sdata, var, self.vars, self.year, self.per, self.crop)