from csv import reader
from numpy import double, zeros, unique, array, where, inf, intersect1d

class CountyDistances(object):
    def __init__(self, cdfile):
        data = []
        with open(cdfile, 'rU') as f:
            for row in reader(f):
                data.append(row)

        data = array(data[1 :]).astype(double) # convert to double array

        self.counties = unique(data[:, 0]).astype(int)

        ncounties = len(self.counties)

        self.closest = zeros((ncounties, ncounties))
        self.dist    = zeros((ncounties, ncounties))
        for i in range(ncounties):
            iscounty = data[:, 0] == self.counties[i]

            self.closest[i] = data[iscounty, 1]
            self.dist[i]    = data[iscounty, 2]
        self.dist *= 1.609344 # convert to km

    def closestCounty(self, fromCounty, toCounties = None, maxDist = inf):
        if fromCounty in self.counties:
            fidx = where(self.counties == fromCounty)[0][0]
        else:
            raise Exception('Cannot find county %d' % fromCounty)
        if toCounties is None:
            closest = self.closest[fidx]
            dist    = self.dist[fidx]
        else:
            closest = intersect1d(self.closest[fidx], toCounties)
            dist    = zeros(len(closest))
            for i in range(len(closest)):
                tidx = where(self.closest[fidx] == closest[i])[0][0]
                dist[i] = self.dist[fidx, tidx]
            sidx = dist.argsort()
            closest = closest[sidx]
            dist = dist[sidx]
        return closest[dist < maxDist], dist[dist < maxDist]