# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 17:32:41 2015

@author: Hongjian
"""

import numpy as np
import matplotlib.pyplot as plt



if __name__ == '__main__':
    
    xlabels = ['ARSON', 'ASSAULT', 'BATTERY', 'BURGLARY', 'CRIM SEXUAL ASSAULT', 
        'CRIMINAL DAMAGE', 'CRIMINAL TRESPASS', 'DECEPTIVE PRACTICE', 
        'GAMBLING', 'HOMICIDE', 'INTERFERENCE WITH PUBLIC OFFICER', 
        'INTIMIDATION', 'KIDNAPPING', 'LIQUOR LAW VIOLATION', 'MOTOR VEHICLE THEFT', 
        'NARCOTICS', 'OBSCENITY', 'OFFENSE INVOLVING CHILDREN', 'OTHER NARCOTIC VIOLATION',
        'OTHER OFFENSE', 'PROSTITUTION', 'PUBLIC INDECENCY', 'PUBLIC PEACE VIOLATION',
        'ROBBERY', 'SEX OFFENSE', 'STALKING', 'THEFT', 'WEAPONS VIOLATION', 'total']
    x = range(len(xlabels))
    
    ylabels = ['#jobs age under 29', 
    '#jobs age from 30 to 54', 
    '#jobs above 55', 
    '#jobs earning under \$1250/month', 
    '#jobs earnings from \$1251 to \$3333/month', 
    '#jobs above \$3333/month',
    '#jobs in goods producing', 
    '#jobs in trade transportation', 
    '#jobs in other services']
    y = range(len(ylabels))
        
        
    type_tag = 'mre2'
    
    d = np.loadtxt('{0}.array'.format(type_tag))
    for i in range(d.shape[0]):
        for j in range(d.shape[1]):
            if abs(d[i,j]) > 1:
                d[i,j] /= abs(d[i,j])
    
    plt.figure(num=1, figsize=(16,8))
    img = plt.matshow(d, fignum=1)
    plt.colorbar(img)
    plt.xticks(x, xlabels, rotation='vertical')
    plt.yticks(y, ylabels)
    plt.savefig('{0}.png'.format(type_tag), format='png')
