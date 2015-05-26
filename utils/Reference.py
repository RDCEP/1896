from csv import reader
from os.path import isfile
from Census import CensusData
from numpy.ma import masked_array, isMaskedArray
from numpy import double, zeros, ones, unique, array, union1d, intersect1d, where, interp, logical_and, arange, sqrt

class ReferenceCombiner(object):
    def __init__(self, yieldfile, yieldirrfile, hareafile, hareairrfile, censusfile, var):
        self.ysum = ReferenceData(yieldfile,    var)
        self.yirr = ReferenceData(yieldirrfile, var)
        self.hsum = ReferenceData(hareafile,    var)
        self.hirr = ReferenceData(hareairrfile, var)

        self.census = CensusData(censusfile, var)

        self.irr = ['ir', 'rf', 'sum']

        # find all counties where some yield and area data are present
        counties1 = union1d(self.ysum.counties, self.yirr.counties)
        counties2 = union1d(self.hsum.counties, self.hirr.counties)
        self.counties = intersect1d(counties1, counties2)

        # pull data
        self.yldsum = self.ysum.getVar()
        self.yldirr = self.yirr.getVar()
        self.hvtsum = self.hsum.getVar()
        self.hvtirr = self.hirr.getVar()

        # interpolate to common counties
        self.yldsum = self.interpolateCounty(self.yldsum, self.ysum.counties, self.counties)
        self.yldirr = self.interpolateCounty(self.yldirr, self.yirr.counties, self.counties)
        self.hvtsum = self.interpolateCounty(self.hvtsum, self.hsum.counties, self.counties)
        self.hvtirr = self.interpolateCounty(self.hvtirr, self.hirr.counties, self.counties)

        # conversion factors for yield and area
        if var in ['maize', 'sorghum']:
            self.yldconv = 2.47105 * 56 / 2.20462
        elif var in ['soybean', 'wheat.spring', 'wheat.winter']:
            self.yldconv = 2.47105 * 60 / 2.20462
        elif var == 'barley':
            self.yldconv = 2.47105 * 48 / 2.20462
        elif var in ['cotton-upland', 'cotton-pima', 'rapeseed']:
            self.yldconv = 2.47105 / 2.20462
        else:
            raise Exception('Unknown crop')
        self.hvtconv = 1 / 2.47105

    def getVar(self, years):
        # interpolate to common times and counties
        frac = self.census.getFrac(years)
        frac = self.interpolateCounty(frac, self.census.counties, self.counties)

        # interpolate to common times
        yldsum = self.interpolateTime(self.yldsum, self.ysum.years, years)
        yldirr = self.interpolateTime(self.yldirr, self.yirr.years, years, fillgaps = False) # no gap filling!
        hvtsum = self.interpolateTime(self.hvtsum, self.hsum.years, years)
        hvtirr = self.interpolateTime(self.hvtirr, self.hirr.years, years, fillgaps = False)

        # extrapolate irrigated yield, sum area, and irrigated area fraction
        yldirr, delta = self.extrapolateYield(yldirr, yldsum, years)
        hvtsum        = self.extrapolateTime(hvtsum, years)
        frac          = self.extrapolateFrac(frac, hvtsum, hvtirr, years)

        ny, nc, ni = len(years), len(self.counties), len(self.irr)
        yld = masked_array(zeros((ny, nc, ni)), mask = ones((ny, nc, ni)))
        hvt = masked_array(zeros((ny, nc, ni)), mask = ones((ny, nc, ni)))
        for i in range(nc):
            for j in range(ny):
                hvt[j, i] = self.computeArea(hvtsum[j, i],  hvtirr[j, i], frac[j, i])
                yld[j, i] = self.computeYield(yldsum[j, i], yldirr[j, i], hvt[j, i], delta[j, i])

            # extrapolate area in time
            for j in range(ni):
                area = hvt[:, i, j]
                if isMaskedArray(area) and area.mask.any() and not area.mask.all():
                    hvt[:, i, j] = interp(years, years[~area.mask], area[~area.mask])

        # convert
        yld *= self.yldconv
        hvt *= self.hvtconv

        return yld, hvt

    def interpolateCounty(self, x, cx, c):
        nt = len(x)
        xnew = masked_array(zeros((nt, len(c))), mask = ones((nt, len(c))))
        for i in range(len(c)):
            if c[i] in cx:
                idx = where(cx == c[i])[0][0]
                xnew[:, i] = x[:, idx]
        return xnew

    def interpolateTime(self, x, yx, y, fillgaps = True):
        nc = x.shape[1]

        xnew = masked_array(zeros((len(y), nc)), mask = ones((len(y), nc)))
        for i in range(nc):
            xc = x[:, i]
            yc = yx

            if isMaskedArray(xc) and not xc.mask.all() and fillgaps:
                yc = yc[~xc.mask]
                xc = xc[~xc.mask]
                xc = interp(arange(yc.min(), yc.max() + 1), yc, xc)
                yc = arange(yc.min(), yc.max() + 1)

            xnew[logical_and(y >= yc.min(), y <= yc.max()), i] = xc[logical_and(yc >= y.min(), yc <= y.max())]

        return xnew

    def extrapolateTime(self, x, y):
        nc = x.shape[1]

        xnew = x.copy()
        for i in range(nc):
            xc = x[:, i]

            if isMaskedArray(xc) and not xc.mask.all():
                xnew[:, i] = interp(y, y[~xc.mask], xc[~xc.mask])

        return xnew

    def extrapolateYield(self, yirr, ysum, years):
        nc = yirr.shape[1]
        nt = len(years)

        eyld = masked_array(zeros((nt, nc)), mask = ones((nt, nc)))
        dmat = masked_array(zeros((nt, nc)), mask = ones((nt, nc)))
        for i in range(nc):
            yi = yirr[:, i]
            ys = ysum[:, i]

            if not isMaskedArray(yi): yi = masked_array(yi, mask = zeros(nt))
            if not isMaskedArray(ys): ys = masked_array(ys, mask = zeros(nt))

            delta = (yi - ys).mean()
            if not isMaskedArray(delta):
                idx = logical_and(yi.mask, ~ys.mask)

                dmat[yi.mask, i] = delta

                # delta shift sum data
                ydelta = ys[idx] + delta

                # variance scale sum data
                ydeltamu = ydelta.mean()
                ydelta2  = ydelta - ydeltamu
                fac      = sqrt(yi.var() / ydelta2.var()) if ydelta2.var() else 1
                ydelta2 *= fac
                ydelta2 += ydeltamu - ydelta2.mean()

                shouldscale = ydelta2 >= ys[idx]
                ydelta[shouldscale] = ydelta2[shouldscale]

                yi[idx] = ydelta

            eyld[:, i] = yi

        return eyld, dmat

    def extrapolateFrac(self, frac, hsum, hirr, years):
        nt, nc = frac.shape

        efrac = masked_array(zeros((nt, nc)), mask = ones((nt, nc)))
        for i in range(nc):
            fc = frac[:, i]
            fh = hirr[:, i] / hsum[:, i]

            if not isMaskedArray(fc): fc = masked_array(fc, mask = zeros(nt))
            if not isMaskedArray(fh): fh = masked_array(fh, mask = zeros(nt))

            fh[~fc.mask] = fc[~fc.mask] # prefer census to survey

            if not fh.mask.all():
                efrac[:, i] = interp(years, years[~fh.mask], fh[~fh.mask])

        return efrac

    def computeArea(self, hsum, hirr, frac):
        hassum = not isMaskedArray(hsum)
        hasirr = not isMaskedArray(hirr)

        if not hassum and not hasirr:
            return masked_array(zeros(3), mask = ones(3))

        if not isMaskedArray(frac): # fraction takes precedence
            if hassum:
                h = array([frac * hsum, (1 - frac) * hsum, hsum])
            else:
                h = array([hirr, (1 - frac) * hirr / frac, hirr / frac])
        else:
            if hassum and hasirr:
                h = array([hirr, max(hsum - hirr, 0), max(hsum, hirr)])
            elif not hasirr:
                h = array([0, hsum, hsum])
            else:
                h = array([hirr, 0, hirr])

        return h

    def computeYield(self, ysum, yirr, area, delta):
        hassum = not isMaskedArray(ysum)
        hasirr = not isMaskedArray(yirr)

        if not hassum and not hasirr:
            return masked_array(zeros(3), mask = ones(3))

        if hassum and hasirr:
            if ysum > yirr: yirr = ysum # temporary fix

            y = masked_array(zeros(3), mask = ones(3))
            if isMaskedArray(area) and area.mask.all(): # no area data
                y[0] = yirr
                y[2] = ysum
            else:
                if area[1] / area[2] >= 0.02:
                    y[0] = yirr
                    y[1] = max((ysum * area[2] - yirr * area[0]) / area[1], 0)
                    y[2] = (area[0] * y[0] + area[1] * y[1]) / area[2]
                else: # no rainfed area
                    y[0] = yirr
                    y[2] = yirr
        elif not hasirr:
            if area[0] > 0 and area[1] > 0:
                y = array([ysum, ysum, ysum]) # assume equal irrigated, rainfed yields
            elif area[0] > 0 and area[1] == 0:
                y = masked_array([ysum, 0, ysum], mask = [0, 1, 0])
            else:
                y = masked_array([0, ysum, ysum], mask = [1, 0, 0])
        else:
            if area[0] > 0 and area[1] > 0:
                y = array([yirr, yirr, yirr])
            elif area[0] == 0 and area[1] > 0:
                y = masked_array([0, yirr, yirr], mask = [1, 0, 0])
            else:
                y = masked_array([yirr, 0, yirr], mask = [0, 1, 0])

        if delta == 0:
            y = masked_array([y[0], 0, y[0]], mask = [0, 1, 0]) # rainfed is nulled out

        return y

class ReferenceData(object):
    def __init__(self, csvfile, var):
        if not isfile(csvfile):
            self.usc      = array([30035]) # random county in montana
            self.year     = array([2000])
            self.value    = masked_array(zeros(1), mask = ones(1)) # no data
            self.years    = unique(self.year)
            self.counties = unique(self.usc)
            return

        data = []
        with open(csvfile, 'rU') as f:
            for row in reader(f):
                data.append(row)

        header = data[0]

        year_idx   = header.index('Year')
        state_idx  = header.index('State ANSI')
        county_idx = header.index('County ANSI')
        data_idx   = header.index('Data Item')
        value_idx  = header.index('Value')

        if var == 'maize':
            label = 'CORN'
        elif var == 'soybean':
            label = 'SOYBEANS'
        elif var == 'sorghum':
            label = 'SORGHUM'
        elif var == 'cotton-upland':
            label = 'COTTON, UPLAND'
        elif var == 'cotton-pima':
            label = 'COTTON, PIMA'
        elif var == 'wheat.spring':
            label = 'WHEAT, SPRING'
        elif var == 'wheat.winter':
            label = 'WHEAT, WINTER'
        elif var == 'barley':
            label = 'BARLEY'
        elif var == 'rapeseed':
            label = 'CANOLA'
        else:
            raise Exception('Unknown crop')

        nd = len(data) - 1

        self.year   = zeros(nd, dtype = int)
        self.state  = zeros(nd, dtype = int)
        self.county = zeros(nd, dtype = int)
        self.data   = zeros(nd, dtype = '|S32')
        self.value  = zeros(nd)
        cnt = 0
        for i in range(nd):
            try:
                line = data[i + 1]
                self.year[cnt]   = int(line[year_idx])
                self.state[cnt]  = int(line[state_idx])
                self.county[cnt] = int(line[county_idx]) if line[county_idx] != '' else 999

                if line[data_idx].startswith(label):
                    self.data[cnt] = var
                else:
                    self.data[cnt] = 'other'

                self.value[cnt] = double(line[value_idx].replace(',', ''))
                cnt += 1
            except:
                print 'Skipping row %d' % (i + 1)

        good_data_idx = logical_and(self.year != 0, self.county != 999)
        good_data_idx = logical_and(good_data_idx,  self.data != 'other') # need to remove!

        self.year   = self.year[good_data_idx]
        self.state  = self.state[good_data_idx]
        self.county = self.county[good_data_idx]
        self.data   = self.data[good_data_idx]
        self.value  = self.value[good_data_idx]

        year_sort_idx = self.year.argsort()

        self.year   = self.year[year_sort_idx]
        self.state  = self.state[year_sort_idx]
        self.county = self.county[year_sort_idx]
        self.data   = self.data[year_sort_idx]
        self.value  = self.value[year_sort_idx]

        self.usc = self.state * 1000 + self.county # unique state-county

        self.years    = unique(self.year)
        self.counties = unique(self.usc)

    def getVar(self):
        nyears, ncounties = len(self.years), len(self.counties)

        var = masked_array(zeros((nyears, ncounties)), mask = ones((nyears, ncounties)))
        for i in range(nyears):
            is_year = self.year == self.years[i]
            for j in range(ncounties):
                is_county = self.usc == self.counties[j]
                is_year_county = logical_and(is_year, is_county)
                if is_year_county.sum():
                    var[i, j] = self.value[is_year_county]

        return var