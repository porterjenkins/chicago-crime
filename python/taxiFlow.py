# -*- coding: utf-8 -*-
"""
Generate the taxi flow in Chicago.


Created on Mon Jan 25 16:19:18 2016

@author: kok
"""


from Crime import Tract
from shapely.geometry import Point
import csv
import numpy as np

import os.path

here = os.path.dirname(os.path.abspath(__file__))





def getTaxiFlow(leaveOut = -1, normalization="bydestination", gridLevel='ca'):
    """
    Retrieve taxi flow from file
    
    the self-flow is set to zero.
    
    LeaveOut define the region to be left out for evaluation. Value 
    ranges from 1 to 77
    
    normalization takes value "none/bydestination/bysource"
    """
    if gridLevel == 'ca':
        s = np.loadtxt("TF.csv", delimiter=",")
    elif gridLevel == 'tract':
        s = np.loadtxt("TF_tract.csv", delimiter=",")
    n = s.shape[0]
    
    for i in range(n):
        s[i,i] = 0
    
    if leaveOut > 0:
        s = np.delete(s, leaveOut -1, 0)
        s = np.delete(s, leaveOut -1, 1)
        
    n = s.shape[0]
        
    assert s.dtype == "float64"
    if normalization == 'bydestination':
        s = np.transpose(s)
        fsum = np.sum(s, axis=1, keepdims=True)
        assert fsum.shape == (n,1)
        s = s / fsum
        assert s.sum() == n and abs(s.sum(axis=1)[9] - 1) <= 0.000000001
    elif normalization == 'bysource':
        fsum = np.sum(s, axis=1, keepdims=True)
        s = s / fsum
        assert s.sum() == n and abs(s.sum(axis=0)[23] - 1) <= 0.000000001
    elif normalization == 'none':
        pass
    
    
    return s



def generateTaxiFlow(gridLevel='ca'):
    """
    Generate taxi flow and write it to a file
    
    This is slow to run
    """
    if gridLevel == 'ca':
        cas = Tract.createAllCAObjects()
    elif gridLevel == 'tract':
        cas = Tract.createAllTractObjects()
    n = len(cas)
    TF = np.zeros((n, n))   # taxi flow matrix
    
    ordKey = sorted(cas.keys())
    
#    cnt = 0
    
    with open('../data/ChicagoTaxi/201401-03.txt', 'rU') as fin:
        reader = csv.reader(fin, delimiter='\t' )
        header = reader.next()
        for row in reader:
            # initialize points            
            start = Point(float(row[3]), float(row[4]))
            end = Point(float(row[5]), float(row[6]))
            
            sid = -1
            eid = -1
            for key, grid in cas.items():
                """
                grid key starts from 1
                map the start/end point of trip into grids to get flow
                """
                if grid.polygon.contains(start):
                    sid = ordKey.index(key)
                if grid.polygon.contains(end):
                    eid = ordKey.index(key)
                if sid != -1 and eid != -1:
                    break
            
            TF[sid, eid] += 1
#            cnt += 1
#            if (cnt > 1000):
#                break
    if gridLevel == 'ca':
        np.savetxt(here + "/TF.csv", TF, delimiter="," )
    elif gridLevel == 'tract':
        np.savetxt(here + "/TF_tract.csv", TF, delimiter="," )






if __name__ == '__main__':
    
#    generateTaxiFlow()
    s = getTaxiFlow(leaveOut=2, normalization="bydestination")