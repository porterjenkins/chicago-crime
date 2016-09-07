"""
Parse chicago crime file

Split Chicago crime by years.
Extract crime count by tracts.
"""

import numpy as np
import matplotlib.pyplot as plt
import shapefile
from shapely.geometry import Polygon, Point, box
import sys
import os
here = os.path.dirname(os.path.abspath(__file__))


class CrimeRecord:
    
    cntBadRecord = 0    # record without GPS is bad
    cntTotal = 0
    CrimeType = ['total']

    def __init__( self, line ):
        ls = line.split(",")
        if len(ls) > 21:
            try:
                self.point = Point( float(ls[-3]), float(ls[-4]) )  # longitude, latitude
                self.id = ls[0]
                self.caseNumber = ls[1]
                self.date = ls[2]
                self.type = ls[5]
                if self.type not in CrimeRecord.CrimeType:
                    CrimeRecord.CrimeType.append(self.type)
                CrimeRecord.cntTotal += 1
            except ValueError:
                self.id = None
                CrimeRecord.cntBadRecord += 1
        else:
            self.id = None
        
        
    def __str__( self ):
        return ' '.join( [self.id, self.caseNumber, self.date, self.type, self.lat, self.lon ] )
        
        
    def getDateField(self, field):
        """
        Get month/day/year/hour/miniute/second field from date
        """
        if field == 'hour':
            hour = int(self.date[11:13])
            # is it PM?
            delta = 12 if hour < 12 and self.date[20:22] == 'PM' else 0
            return hour + delta
        else:
            return self.date
            
        

        
class CrimeDataset:
    
    def __init__( self, fname ):
        self.f = open( fname, 'r' )
        
        
    def crimeCount_PerTract( self, tracts ):
        """
        count the number of crimes for each tract
        
        Input:
            tracts - a map of tract ID to tract object
        """
        for line in self.f:
            cr = CrimeRecord( line )
            if cr.id != None:
                for tract in tracts.values():
                    if tract.containCrime (cr):
                        tract.count['total'] += 1
                        if cr.type not in tract.count:
                            tract.count[cr.type] = 1
                        else:
                            tract.count[cr.type] += 1
                            


    def temporalDistribution_perTract_perCategory(self, areas):
        """
        Generate the temporal distribution of crime occurrences over 
        each category for each area
        """
        for line in self.f:
            cr = CrimeRecord(line)
            if cr.id != None:
                for area in areas.values():
                    if area.containCrime(cr):
                        hoc = cr.getDateField('hour')
                        if cr.type not in area.timeHist:
                            area.timeHist[cr.type] = np.zeros(24)
                        area.timeHist[cr.type][hoc] += 1
                        area.timeHist['total'][hoc] += 1
                        
                        
            
        
        
    @classmethod
    def splitFileIntoYear( cls, rawfileName ):
        """
        Split the raw file according to the year filed
        """
        cls.f = open(rawfileName, 'r')
        header = cls.f.readline()  # get rid of header line
        years = {}
        for line in cls.f:
            cr = CrimeRecord(line)
            year = cr.date[6:10]
            if year not in years:
                years[year] = open(here + '/../data/chicago-crime-{0}.csv'.format(year), 'w')
            years[year].write(line)
            
        for F in years.values():
            F.close()
            
            
   
        
        
class Tract:
    
    
    def __init__( self, shp, rec=None ):
        """
        Build one Tract object from the shapefile._Shape object
        """
        self.bbox = box(*shp.bbox)
        self.polygon = Polygon(shp.points)
        self.count = {'total': 0} # type: value
        self.timeHist = {'total': np.zeros(24)}
        if rec != None:
            self.CA = rec[7]
        
        
    
    def containCrime( self, cr ):
        """
        return true if the cr record happened within current tract
        """
        if self.bbox.contains(cr.point):
            if self.polygon.contains(cr.point):
                return True
        return False
        
        
    
    def plotTimeHist(self, keys=None):
        """
        Plot the crime time histogram
        """
        if len(self.timeHist) == 1:
            return
        else:
            if keys is None:
                keys = self.timeHist.keys()
            values = [self.timeHist[key] for key in keys]
            
            plt.figure()
            for val in values:
                plt.plot(val)
            plt.legend(keys)
            plt.show()
            
            
        
        
    @classmethod
    def createAllTractObjects( cls ):
        cls.sf = shapefile.Reader(here + '/../data/chicago-shp-2010-gps/chicago_tract_wgs84')
        cls.tracts = {}
        
        shps = cls.sf.shapes()
        for idx, shp in enumerate(shps):
            rec = cls.sf.record(idx)
            tid = int(rec[3])
            trt = Tract(shp, rec)
            cls.tracts[tid] = trt
        
        return cls.tracts
            
            
            
            
    @classmethod
    def createAllCAObjects( cls ):
        cls.casf = shapefile.Reader(here + '/../data/ChiCA_gps/ChiCaGPS')
        cls.cas = {}
        
        shps = cls.casf.shapes()
        for idx, shp in enumerate(shps):
            tid = cls.casf.record(idx)[4]
            trt = Tract(shp)
            cls.cas[int(tid)] = trt
            
        return cls.cas



def main():
    """
    Commandline tool
    1. split crime file by years
    2. generate crime count for each tract in given year
    """
    year = 2010
    arguments = {}
    if len(sys.argv) % 2 == 1:
        for i in range(1, len(sys.argv), 2):
            arguments[sys.argv[i]] = sys.argv[i+1]
    else:
        print """Usage: Crime.py [options] [value]
        Possible options:
            year       e.g. 2010 default '2010'
            splitfile  e.g. true default false"""

    if 'splitfile' in arguments:
        if arguments['splitfile'] == 'true':
            CrimeDataset.splitFileIntoYear(here + '/../data/Crimes_-_2001_to_present.csv')
            return 0
            
    if 'year' in arguments:
        year = arguments['year']
        
    foutName = here + '/../data/chicago-crime-tract-level-{0}.csv'.format(year)
    
    if os.path.exists(foutName):
        print 'The year {0} is already merged.\nQuit Program'.format(year)
        return 0
            
    
    c = CrimeDataset(here + '/../data/chicago-crime-{0}.csv'.format(year))
    T = Tract.createAllTractObjects()
    c.crimeCount_PerTract(T)    
    CrimeRecord.CrimeType.sort()
    cntKey = CrimeRecord.CrimeType
    print 'Write tract level crime file for year {0}'.format(year)
    print len(cntKey), cntKey
        
    with open(foutName, 'w') as fout:
        fout.write(','.join( ['tractID'] + cntKey) + '\n' )
        for k, v in T.items():
            cntstr = []
            for tp in cntKey:
                if tp in v.count:
                    cntstr.append( str(v.count[tp]) )
                else:
                    cntstr.append('0')
            fout.write(','.join( [str(k)] + cntstr ))
            fout.write("\n")
            
    print "Bad records: {0}".format(CrimeRecord.cntBadRecord)
    print "Total records: {0}".format(CrimeRecord.cntTotal)          




def crime_time_histogram(year=2010):
    CA = Tract.createAllCAObjects()
    c = CrimeDataset("../data/chicago-crime-{0}.csv".format(year))
    c.temporalDistribution_perTract_perCategory(CA)
    return CA
    
    
        
if __name__ == '__main__':
#    main()
    ca = crime_time_histogram()
    
