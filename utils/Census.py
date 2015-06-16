from csv import reader
from numpy.ma import masked_array
from numpy import double, zeros, ones, unique, logical_and, intersect1d, interp

class CensusData(object):
    def __init__(self, csvfile, var):
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
            sum_area_label = 'CORN, GRAIN - ACRES HARVESTED'
            irr_area_label = 'CORN, GRAIN, IRRIGATED - ACRES HARVESTED'
        elif var == 'soybean':
            sum_area_label = 'SOYBEANS - ACRES HARVESTED'
            irr_area_label = 'SOYBEANS, IRRIGATED - ACRES HARVESTED'
        elif var == 'sorghum':
            sum_area_label = 'SORGHUM, GRAIN - ACRES HARVESTED'
            irr_area_label = 'SORGHUM, GRAIN, IRRIGATED - ACRES HARVESTED'
        elif var == 'cotton-upland':
            sum_area_label = 'COTTON, UPLAND - ACRES HARVESTED'
            irr_area_label = 'COTTON, UPLAND, IRRIGATED - ACRES HARVESTED'
        elif var == 'cotton-pima':
            sum_area_label = 'COTTON, PIMA - ACRES HARVESTED'
            irr_area_label = 'COTTON, PIMA, IRRIGATED - ACRES HARVESTED'
        elif var == 'wheat.spring':
            sum_area_label = 'WHEAT, SPRING, (EXCL DURUM) - ACRES HARVESTED'
            irr_area_label = 'WHEAT, SPRING, (EXCL DURUM), IRRIGATED - ACRES HARVESTED'
        elif var == 'wheat.winter':
            sum_area_label = 'WHEAT, WINTER - ACRES HARVESTED'
            irr_area_label = 'WHEAT, WINTER, IRRIGATED - ACRES HARVESTED'
        elif var == 'barley':
            sum_area_label = 'BARLEY - ACRES HARVESTED'
            irr_area_label = 'BARLEY, IRRIGATED - ACRES HARVESTED'
        elif var == 'rapeseed':
            sum_area_label = 'CANOLA - ACRES HARVESTED'
            irr_area_label = 'CANOLA, IRRIGATED - ACRES HARVESTED'
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

                dat = line[data_idx]
                if dat == sum_area_label:
                    self.data[cnt] = 'sum'
                elif dat == irr_area_label:
                    self.data[cnt] = 'irr'
                else:
                    self.data[cnt] = 'other'

                value = line[value_idx].strip().replace(',', '')
                self.value[cnt] = double(value) if value != '(D)' else -999

                cnt += 1
            except:
                print 'Skipping row %d' % (i + 1)

        good_data_idx = logical_and(self.year != 0, self.value != -999)

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

        if var == 'wheat.winter':
            # assign all winter wheat variables to previous calendar year
            self.year -= 1

        self.years    = unique(self.year)
        self.counties = unique(self.usc)

    def getVar(self, varname):
        nyears, ncounties = len(self.years), len(self.counties)

        var = masked_array(zeros((nyears, ncounties)), mask = ones((nyears, ncounties)))

        is_var = self.data == varname # no cleaning?
        for i in range(nyears):
            is_year = self.year == self.years[i]
            is_var_year = logical_and(is_var, is_year)
            for j in range(ncounties):
                is_county = self.usc == self.counties[j]
                is_var_year_county = logical_and(is_var_year, is_county)
                if is_var_year_county.sum():
                    var[i, j] = self.value[is_var_year_county]

        return var

    def getFrac(self, years):
        irrdata = self.getVar('irr')
        sumdata = self.getVar('sum')

        sh = (len(years), len(self.counties))
        frac = masked_array(zeros(sh), mask = ones(sh))
        for i in range(len(self.counties)):
            irrmask = masked_array(irrdata[:, i]).mask
            summask = masked_array(sumdata[:, i]).mask

            if not irrmask.all() and not summask.all(): # both data
                irryears = self.years[~irrmask]
                sumyears = self.years[~summask]

                cyears  = intersect1d(irryears, sumyears)
                ncyears = len(cyears)
                if ncyears:
                    f = zeros(ncyears)
                    for j in range(ncyears):
                        f[j]  = irrdata[self.years == cyears[j], i]
                        f[j] /= sumdata[self.years == cyears[j], i]
                    frac[:, i] = interp(years, cyears, f)

        return frac