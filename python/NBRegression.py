"""
Run the Negative Binomial Regression model

The regresion model use various features to predict the crime count in each
unit of study area (i.e. tract or Community Area)

Author: Hongjian
date:8/20/2015
"""


"""
Part One
Generate vairous features

factor into separate file FeatureUtils
"""

from FeatureUtils import *


"""
Part Two
Regression models
"""


import numpy as np
from scipy import stats
from scipy.stats import nbinom
from scipy.special import gammaln
from statsmodels.base.model import GenericLikelihoodModel


"""
Part Three
build model and compare
"""

import pandas as pd
from sklearn.preprocessing import scale
import statsmodels.api as sm
from sklearn import cross_validation

# misc libraries
import matplotlib.pyplot as plt
import subprocess
import os.path
import os
import random
from itertools import combinations
from sklearn.utils import shuffle


    
"""
Part Two
Regression models
"""



def linearRegression(features, Y):
    """
    learn the linear regression model from features to Y
    output the regression analysis parameters
    plot scatter plot
    """
    mod = sm.OLS(Y, features )
    res = mod.fit()
    return res


    
    

class NegBin(GenericLikelihoodModel):
    """
    negative binomial regression
    """
    
    def __init__(self, endog, exog, **kwds):
        super(NegBin, self).__init__(endog, exog, **kwds)
        
        
    def nloglikeobs(self, params):
        alpha = params[-1]
        beta = params[:-1]
        mu = np.exp(np.dot(self.exog, beta))
        size = 1 / alpha
        prob = size / (size+mu)
      #  ll = 0
        # for idx, y in enumerate(self.endog):
         #    ll += gammaln(y + size) - gammaln(size) - gammaln(y+1) + y * np.log(mu * alpha / (mu *alpha + 1))- size * np.log(mu * alpha + 1)
        ll = nbinom.logpmf( self.endog, size, prob)
        return -ll
        
    def fit(self, start_params=None, maxiter = 10000, maxfun=10000, **kwds):
        if start_params == None:
            start_params = np.append(np.zeros(self.exog.shape[1]), .5)
            if self.exog.mean() > 1:
                start_params[:-1] = np.ones(self.exog.shape[1]) * np.log(self.endog.mean())  / self.exog.mean()
            else:
                start_params[:-1] = np.ones(self.exog.shape[1]) * np.log(self.endog.mean())
#            print "endog mean:", self.endog.mean(), "log endog mean:", np.log(self.endog.mean())
#            print "exog mean", self.exog.mean()
        return super(NegBin, self).fit(start_params=start_params, maxiter=maxiter,
                maxfun=maxfun, **kwds)
                
    
    def predict(self, params, exog=None, *args, **kwargs):
        """
        predict the acutal endogenous count from exog
        """
        beta = params[:-1]
        return np.exp(exog.dot(beta))
  


    
def negativeBinomialRegression(features, Y):
    """
    learn the NB regression
    """
    mod = NegBin(Y, features)
    res = mod.fit(disp=False)
    if not res.mle_retvals['converged']:
        print "NBreg not converged.", res.params[0], ",", res.pvalues[0]
    return res, mod


    
def unitTest_withOnlineSource():
    import patsy
    import pandas as pd
    url = 'http://vincentarelbundock.github.com/Rdatasets/csv/COUNT/medpar.csv'
    medpar = pd.read_csv(url)
    y, X = patsy.dmatrices('los~type2+type3+hmo+white', medpar)
    res = negativeBinomialRegression(X, y)
    return y, X, medpar
    
    
def unitTest_onChicagoCrimeData():

    W = generate_transition_SocialLag(2010)
    Yhat = retrieve_crime_count(2009, -1)
    Y = retrieve_crime_count(2010, -1)
#    i = retrieve_income_features()
#    e = retrieve_education_features()
#    r = retrieve_race_features()
#    C = generate_corina_features()
        
    f1 = np.dot(W, Yhat)
    # f = np.concatenate((f1, i[1], e[1], r[1], np.ones(f1.shape)), axis=1)
    # f = pd.DataFrame(f, columns=['social lag'] + i[0] + e[0] + r[0] + ['intercept'])
#    f = scale(f)
#    f = np.concatenate((f, np.ones(f1.shape)), axis=1)
    f = np.concatenate( (C[1], np.ones(f1.shape)), axis=1 )
    np.savetxt("Y.csv", Y, delimiter=",")
    f = pd.DataFrame(f, columns=C[0] + ['intercept'])
    f.to_csv("f.csv", sep="," )
    Y = Y.reshape((77,))
    print "Y", Y.mean()
    res = negativeBinomialRegression(f, Y)
    
    
    print "f shape", f.shape
    print "Y shape", Y.shape
    linearRegression(f, Y)
    return res
     
    




"""
Part Three

Evaluation and fitting real models on Chicago data.
"""



def leaveOneOut_evaluation_onChicagoCrimeData(year=2010, features= ["all"], crime_idx=-1, flow_type=0, verboseoutput=False):
    """
    Generate the social lag from previous year
    use income/race/education of current year
    """
    W = generate_transition_SocialLag(year, lehd_type=flow_type)
    Yhat = retrieve_crime_count(year-1, crime_idx)
    Y = retrieve_crime_count(year, crime_idx)
    C = generate_corina_features()
    popul = C[1][:,0].reshape((77,1))
    
    # crime count is normalized by the total population as crime rate
    # here we use the crime count per 10 thousand residents
    Y = np.divide(Y, popul) * 10000
    Yhat = np.divide(Yhat, popul) * 10000
    
    W2 = generate_geographical_SpatialLag_ca()
    
    i = retrieve_income_features()
    e = retrieve_education_features()
    r = retrieve_race_features()
    
    f1 = np.dot(W, Y)
    f2 = np.dot(W2, Y)
    # add intercept
    columnName = ['intercept']
    f = np.ones(f1.shape)

    if "all" in features:
        f = np.concatenate( (f, f1, i[1], e[1], r[1]), axis=1)
        f = pd.DataFrame(f, columns=['social lag'] + i[0] + e[0] + r[0])
    if "sociallag" in features: 
        f = np.concatenate( (f, f1), axis=1)
        columnName += ['social lag']
    if  "income" in features:
        f = np.concatenate( (f, i[1]), axis=1)
        columnName += i[0]
    if "race" in features:
        f = np.concatenate( (f, r[1]), axis=1)
        columnName += r[0]
    if "education" in features :
        f = np.concatenate( (f, e[1]), axis=1)
        columnName += e[0]
    if 'corina' in features :
        f = np.concatenate( (f, C[1]), axis=1)
        columnName += C[0]
    if 'spatiallag' in features:
        f = np.concatenate( (f, f2), axis=1)
        columnName += ['spatial lag']
    if 'temporallag' in features:
        f = np.concatenate( (f, Yhat), axis=1)
        columnName += ['temporal lag']
    f = pd.DataFrame(f, columns = columnName)

        
    # call the Rscript to get Negative Binomial Regression results
    np.savetxt("Y.csv", Y, delimiter=",")
    f.to_csv("f.csv", sep=",", index=False)
    if verboseoutput:
        subprocess.call( ['Rscript', 'nbr_eval.R', 'verbose'] )
    else:
        nbres = subprocess.check_output( ['Rscript', 'nbr_eval.R'] )
    
    Y = Y.reshape((77,))
    loo = cross_validation.LeaveOneOut(77)
    mae = 0
    mae2 = 0
    errors1 = []
    errors2 = []
    for train_idx, test_idx in loo:
        f_train, f_test = f.loc[train_idx], f.loc[test_idx]
        Y_train, Y_test = Y[train_idx], Y[test_idx]
#        res, mod = negativeBinomialRegression(f_train, Y_train)
#        ybar = mod.predict(res.params, exog=f_test)
#        errors1.append( np.abs(Y_test - ybar.values[0])[0] )


        r2 = linearRegression(f_train, Y_train)
        y2 = r2.predict(f_test)
        errors2.append( np.abs( Y_test - y2 ) )
#        print test_idx, Y_test[0], ybar.values[0], y2[0]
        if verboseoutput:
            print Y_test[0], y2[0]
        
#    mae = np.mean(errors1)
    mae2 = np.mean(errors2)
#    var = np.sqrt( np.var(errors1) )
    var2 = np.sqrt( np.var(errors2) )
#    mre = mae / Y.mean()
    mre2 = mae2 / Y.mean()
#    print "NegBio Regression MAE", mae, "std", var, "MRE", mre
    if verboseoutput:
        print "Linear Regression MAE", mae2, "std", var2, "MRE", mre2
    else:
        print nbres
        print mae2, var2, mre2
        return np.array([[float(e) for e in nbres.split(" ")], [mae2, var2, mre2]])
    



def tenFoldCV_onChicagoCrimeData(features=['corina'], CVmethod='10Fold', P = 10, NUM_ITER=20, SHUFFLE=True):
    """
    Use different years data to train the NB model
    """
    YEARS = range(2003, 2014)
    
    Y = []
    C = []
    FL = []
    GL = []
    T = []
    for year in YEARS:
        W = generate_transition_SocialLag(year, lehd_type=0)
        Yhat = retrieve_crime_count(year-1, -1)
        y = retrieve_crime_count(year, -1)
        c = generate_corina_features()
        popul = c[1][:,0].reshape((77,1))
        
        # crime count is normalized by the total population as crime rate
        # here we use the crime count per 10 thousand residents
        y = np.divide(y, popul) * 10000
        Yhat = np.divide(Yhat, popul) * 10000
        
        W2 = generate_geographical_SpatialLag_ca()
        
        f1 = np.dot(W, Yhat)
        f2 = np.dot(W2, Yhat)
        
        FL.append(f1)
        GL.append(f2)
        Y.append(y)
        T.append(Yhat)
        C.append(c[1])
    
    
    Y = np.concatenate(Y, axis=0)
    columnName = ['intercept']
    f = np.ones(Y.shape)
    if 'corina' in features:
        C = np.concatenate(C, axis=0)
        f = np.concatenate( (f, C), axis=1 )
        columnName += c[0]
    if 'sociallag' in features:
        FL = np.concatenate(FL, axis=0)
        f = np.concatenate( (f, FL), axis = 1)
        columnName += ['sociallag']
    if 'spatiallag' in features:
        GL = np.concatenate(GL, axis=0)
        f = np.concatenate((f, GL), axis=1)
        columnName += ['spatiallag']
    if 'temporallag' in features:
        T = np.concatenate(T, axis=0)
        f = np.concatenate((f, T), axis=1)
        columnName += ['temporallag']
    
    
    
    if SHUFFLE:
        f, Y = shuffle(f, Y)
    
    if CVmethod == '10Fold':
        splt = cross_validation.KFold(n=f.shape[0], n_folds=10, shuffle=True)
    elif CVmethod == 'leaveOneOut':
        splt = cross_validation.LeaveOneOut(n=f.shape[0])
    elif CVmethod == 'leavePOut':
        splt = cross_validation.LeavePOut(n=f.shape[0], p = P)
    
    mae1 = []
    mae2 = []
    mre1 = []
    mre2 = []
    sd_mae1 = []
    sd_mae2 = []
    sd_mre1 = []
    sd_mre2 = []
    med_mae1 = []
    med_mae2 = []
    med_mre1 = []
    med_mre2 = []
    cnt = 0
    
    if CVmethod == 'leaveOneOut':
        y_gnd = []
        y_nb = []
        y_lr = []


    for train_idx, test_idx in splt:
        cnt += 1
        if cnt > NUM_ITER:
            break
        f_train, f_test = f[train_idx, :], f[test_idx, :]
        Y_train, Y_test = Y[train_idx, :], Y[test_idx, :]
        

        # write file for invoking NB regression in R        
        np.savetxt("Y_train.csv", Y_train, delimiter=",")
        np.savetxt("Y_test.csv", Y_test, delimiter=",")        
        pd.DataFrame(f_train, columns = columnName).to_csv("f_train.csv", sep=",", index=False)
        pd.DataFrame(f_test, columns = columnName).to_csv("f_test.csv", sep=",", index=False)
        
        # NB regression 
        nbres = subprocess.check_output( ['Rscript', 'nbr_eval_kfold.R'] ).split(" ")
        y1 = np.array([float(e) for e in nbres])
        y1 = y1.reshape((y1.shape[0], 1))
        a = np.abs( Y_test - y1 )
        
        mae1.append(np.mean(a))
        sd_mae1.append(np.std(a))
        med_mae1 += a.tolist()
        r = a / Y_test
        mre1.append(np.mean(r))
        sd_mre1.append(np.std(r))
        med_mre1 += r.tolist()
        
        # Linear regression
        r2 = linearRegression(f_train, Y_train)
        y2 = r2.predict(f_test)
        y2 = y2.reshape((y2.shape[0], 1))
        ae = np.abs(Y_test - y2)
        mae2.append( np.mean(ae) )
        sd_mae2.append( np.std(ae) )
        med_mae2 += ae.tolist()
        re = ae / Y_test
        mre2.append( np.mean(re))
        sd_mre2.append( np.std(re) )
        med_mre2 += re.tolist()
        
        if CVmethod == 'leaveOneOut':
            y_gnd.append(Y_test)
            y_lr.append(y2)
    
    
    if CVmethod == 'leaveOneOut':
        print np.mean(mae1), np.median(mae1), np.mean(mre1), np.median(mre1),
        print np.mean(mae2), np.median(mae2), np.mean(mre2), np.median(mre2)
        return y_gnd, y_lr
    else:
        print np.mean(mae1), np.mean(sd_mae1), np.median(med_mae1), np.mean(mre1), np.mean(sd_mre1), np.median(med_mre1),
        print np.mean(mae2), np.mean(sd_mae2), np.median(med_mae2), np.mean(mre2), np.mean(sd_mre2), np.median(med_mre2)
        
    return mae1, mae2



def permutationTest_onChicagoCrimeData(year=2010, features= ["all"], iters=1001):
    """
    Permutation test with regression model residuals
    
    How to do the permutation?
    
    Initial try - before 2015/10/4
    
    For each sample point (CA), we permute the dependent variable (crime count),
    while keeps the dependent variables the same.
    
    This approach is hard to explain.
    
    
    Second try:
    permute the feature of interest
    """
    W = generate_transition_SocialLag(year)
    Yhat = retrieve_crime_count(year-1, -1)
    Y = retrieve_crime_count(year, -1)
    C = generate_corina_features()
    popul = C[1][:,0].reshape((77,1))
    
    # crime count is normalized by the total population as crime rate
    # here we use the crime count per 10 thousand residents
#    Y = np.divide(Y, popul) * 10000
#    Yhat = np.divide(Yhat, popul) * 10000
    
    W2 = generate_geographical_SpatialLag_ca()
    
    i = retrieve_income_features()
    e = retrieve_education_features()
    r = retrieve_race_features()
    
    f1 = np.dot(W, Y)
    f2 = np.dot(W2, Y)
    # add intercept
    columnName = ['intercept']
    f = np.ones(f1.shape)

    if "all" in features:
        f = np.concatenate( (f, f1, i[1], e[1], r[1]), axis=1)
        f = pd.DataFrame(f, columns=['social lag'] + i[0] + e[0] + r[0])
    if "sociallag" in features: 
        f = np.concatenate( (f, f1), axis=1)
        columnName += ['social lag']
    if  "income" in features:
        f = np.concatenate( (f, i[1]), axis=1)
        columnName += i[0]
    if "race" in features:
        f = np.concatenate( (f, r[1]), axis=1)
        columnName += r[0]
    if "education" in features :
        f = np.concatenate( (f, e[1]), axis=1)
        columnName += e[0]
    if 'corina' in features :
        flr = np.array(f, copy=True)
        flr = np.concatenate( (flr, C[1]), axis=1)
        C[1][:,0] = np.log(C[1][:,0])
        f = np.concatenate( (f, C[1]), axis=1)
        columnName += C[0]
    if 'spatiallag' in features:
        f = np.concatenate( (f, f2), axis=1)
        flr = np.concatenate( (flr, f2), axis=1 )
        columnName += ['spatial lag']
    if 'temporallag' in features:
        f = np.concatenate( (f, Yhat), axis=1)
        flr = np.concatenate( (flr, Yhat), axis=1 )
        columnName += ['temporal lag']
    f = pd.DataFrame(f, columns = columnName)
    flr = pd.DataFrame(flr, columns = columnName)
        
    
    # permute each column
    for idx, columnKey in enumerate(columnName):
        print 'Process independent variable {0}'.format(columnKey)
        if columnKey == 'intercept':
            continue
            
        # initialization
        LR_coeffs = []
        if os.path.exists('coefficients.txt'):
            os.remove('coefficients.txt')
            
        for i in range(iters):
            if i == 0:
                pidx = range(len(Y))
            else:
                pidx = np.random.permutation(len(Y))
            
            # permute the column
            f[columnKey] = f[columnKey].values[pidx]
            # call the Rscript to get Negative Binomial Regression results         
            f.to_csv("f.csv", sep=",", index=False)
            np.savetxt("Y.csv", Y, delimiter=",")
            subprocess.call( ['Rscript', 'nbr_permutation_test.R'] )
            
            
            # LR permutation test
            flr[columnKey] = flr[columnKey].values[pidx]
            lrmod = linearRegression(flr, Y)
            LR_coeffs.append(lrmod.params)
            
        NB_coeffs = np.loadtxt(fname='coefficients.txt', delimiter=',')
        LR_coeffs = np.array(LR_coeffs)
        
        
        # process columns: distribution of permutations
        
        column = NB_coeffs[:,idx]
        targ = column[0]
        cnt = 0.0
        for e in column:
            if e > targ:
                cnt += 1
        nb_p = cnt / len(column)
                
        lr_col = LR_coeffs[:,idx]
        lr_trg = lr_col[0]
        lr_cnt = 0.0
        for e in lr_col:
            if e > lr_trg:
                lr_cnt += 1
        lr_p = lr_cnt / len(column)       
                
        print columnKey, targ, nb_p, lr_trg, lr_p
        
        plt.figure(figsize=(8,3))
        # NB
        plt.subplot(1,2,1)
        plt.hist(column)
        plt.axvline(x = targ, linewidth=4, color='r')
        plt.title("NB {0} p {1:.4f}".format(columnName[idx], nb_p))
        # LR
        plt.subplot(1,2,2)
        plt.hist(lr_col)
        plt.axvline(x = lr_trg, linewidth=4, color='r')
        plt.title("LR {0} p {1:.4f}".format(columnName[idx], lr_p))
        plt.savefig('PT-{0}.png'.format(columnKey), format='png')
    
    
    
    
    


def crimeRegression_eachCategory(year=2010):
    header = ['ARSON', 'ASSAULT', 'BATTERY', 'BURGLARY', 'CRIM SEXUAL ASSAULT', 
    'CRIMINAL DAMAGE', 'CRIMINAL TRESPASS', 'DECEPTIVE PRACTICE', 
    'GAMBLING', 'HOMICIDE', 'INTERFERENCE WITH PUBLIC OFFICER', 
    'INTIMIDATION', 'KIDNAPPING', 'LIQUOR LAW VIOLATION', 'MOTOR VEHICLE THEFT', 
    'NARCOTICS', 'OBSCENITY', 'OFFENSE INVOLVING CHILDREN', 'OTHER NARCOTIC VIOLATION',
    'OTHER OFFENSE', 'PROSTITUTION', 'PUBLIC INDECENCY', 'PUBLIC PEACE VIOLATION',
    'ROBBERY', 'SEX OFFENSE', 'STALKING', 'THEFT', 'WEAPONS VIOLATION', 'total']
    W = generate_transition_SocialLag(year)
    i = retrieve_income_features()
    e = retrieve_education_features()
    r = retrieve_race_features()
    predCrimes = {}
    unpredCrimes = {}
    for idx, val in enumerate(header):
        Y = retrieve_crime_count(year, idx+1)
        
        f1 = np.dot(W, Y)
        f = np.concatenate( (f1, np.ones(f1.shape)), axis=1 )
        Y = Y.reshape((77,))
        
        # linearRegression(f1, Y)
        cnt = 0
        for z in Y:
            if z == 0:
                cnt += 1
        print ",".join( [val, str(cnt), ""] ),  # sparseness
        res = negativeBinomialRegression(f, Y)
        if res.mle_retvals['converged']:
            predCrimes[val] = [cnt, len(Y)]
        else:
            unpredCrimes[val] = [cnt, len(Y)]
        
    return predCrimes, unpredCrimes
    
    
    

def generate_flowType_crimeCount_matrix():
    """
    The result is used in ./plotMat.py/plot_flowType_crimeCount() function.
    
    Results shown on the wikispace:
    https://wikispaces.psu.edu/display/LSP/Social+flow%2C+Crime
    
    9/18/2015 Under which scenarios does the social lag help the most?
    """
    
    header = ['ARSON', 'ASSAULT', 'BATTERY', 'BURGLARY', 'CRIM SEXUAL ASSAULT', 
    'CRIMINAL DAMAGE', 'CRIMINAL TRESPASS', 'DECEPTIVE PRACTICE', 
    'GAMBLING', 'HOMICIDE', 'INTERFERENCE WITH PUBLIC OFFICER', 
    'INTIMIDATION', 'KIDNAPPING', 'LIQUOR LAW VIOLATION', 'MOTOR VEHICLE THEFT', 
    'NARCOTICS', 'OBSCENITY', 'OFFENSE INVOLVING CHILDREN', 'OTHER NARCOTIC VIOLATION',
    'OTHER OFFENSE', 'PROSTITUTION', 'PUBLIC INDECENCY', 'PUBLIC PEACE VIOLATION',
    'ROBBERY', 'SEX OFFENSE', 'STALKING', 'THEFT', 'WEAPONS VIOLATION', 'total']
    
    errors = np.zeros((9, len(header)))
    mre1 = np.zeros((9, len(header)))
    mre2 = np.zeros((9, len(header)))
    for idx, val in enumerate(header):
        for j in range(9):
            r1 = leaveOneOut_evaluation_onChicagoCrimeData(2010, ['corina'], crime_idx=idx+1, flow_type=j)
            r2 = leaveOneOut_evaluation_onChicagoCrimeData(2010, ['corina', 'sociallag'], crime_idx=idx+1, flow_type=j)
            mre1[j][idx] = r1[0,2]
            mre2[j][idx] = r2[0,2]
            errors[j][idx] = r1[0,2] - r2[0,2]
    np.savetxt('errors.array', errors)
    np.savetxt('mre1.array', mre1)
    np.savetxt('mre2.array', mre2)
    
    
    
    
if __name__ == '__main__':
    # generate_geographical_SocialLag('../data/chicago-CA-geo-neighbor')
   
#   crimeRegression_eachCategory()
    # f = unitTest_onChicagoCrimeData()
#   print f.summary()

    
   # leaveOneOut_evaluation_onChicagoCrimeData(2010, ['corina', 'sociallag'], verboseoutput=False)
   permutationTest_onChicagoCrimeData(2010, ['corina', 'sociallag', 'spatiallag', 'temporallag'])
    
#    CV = '10Fold'
#    feat_candi = ['corina', 'spatiallag', 'temporallag', 'sociallag']
#    for i in range(1,5):
#        f_lists = combinations(feat_candi, i)
#        for f in f_lists:
#            print '+'.join(f),
#            if CV == '10Fold':
#                r = tenFoldCV_onChicagoCrimeData(f)
#            else:
#                r = tenFoldCV_onChicagoCrimeData(f, CVmethod='leaveOneOut')
    
    
    # Ps = range(1, 5) + range(10, 81, 20)
    # for p in Ps:
        # print p,
        # s1, s2 = tenFoldCV_onChicagoCrimeData(['temporallag'], CVmethod='leavePOut', P=p, NUM_ITER=20)
    
#    for num_iter in range(10, 41, 5):
#        print num_iter,
#        s1,s2 = tenFoldCV_onChicagoCrimeData(['temporallag'], CVmethod='leaveOneOut', NUM_ITER=20, SHUFFLE=False)