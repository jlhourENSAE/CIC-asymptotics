#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main functions to generate data and analyze performance

Created on Wed Nov 11 12:07:14 2020

@author: jeremylhour
"""

import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt


########## UNOBSERVED RANKS ##########

def true_theta(distrib_y, distrib_z, distrib_x, size = 10000):
    """
    true_theta:
        compute the true value of theta,
        by simulation since analytical formula is not possible.
        
    :param distrib_y: distribution of Y
    :param distrib_z: distribution of Z
    :param distrib_x: distribution of X
    """
    Q_y = distrib_y.ppf # Quantile function of Y
    F_z = distrib_z.cdf # CDF of Z
    Q_x = distrib_x.ppf # Quantile function of X
    
    U = np.random.uniform(size=size)
    U_tilde = Q_y(F_z(Q_x(U)))
    theta = U_tilde.mean()
    return theta


def analytical_theta(alpha_y, lambda_z, lambda_x):
    """
    analytical_theta:
        compute the true value of theta,
        using an analytical formula.
    
    :param alpha_y:
    :param lambda_z:
    :param lambda_x:
    """
    theta = 1/(alpha_y*lambda_x/lambda_z - 1)
    return theta


def generate_data(distrib_y, distrib_z, distrib_x, size = 1000):
    """
    generate_data:
        generate data following the specified distributions.
        Should be of class "rv_continuous" from scipy.stats
        
    :param distrib_y: distribution of Y, instance of rv_continuous
    :param distrib_z: distribution of Z, instance of rv_continuous
    :param distrib_x: distribution of X, instance of rv_continuous
    :param size: sample size for each vector
    """        
    y = distrib_y.ppf(np.random.uniform(size=size))  
    z = distrib_z.ppf(np.random.uniform(size=size)) 
    x = distrib_x.ppf(np.random.uniform(size=size))   
    #theta0 = true_theta(distrib_y=distrib_y, distrib_z=distrib_z, distrib_x=distrib_x, size = 100000)
    
    return y, z, x


########## OBSERVED RANKS ##########

def true_theta_observed_rank(distrib_y, distrib_u, size = 10000):
    """
    true_theta:
        compute the true value of theta,
        by simulation since analytical formula is not possible.
        
    :param distrib_y: distribution of Y
    :param distrib_u: distribution of U
    """
    Q_y = distrib_y.ppf # Quantile function of Y
    Q_u = distrib_u.ppf # Quantile function of U
    
    U = np.random.uniform(size=size)
    U_tilde = Q_y(Q_u(U))
    theta = U_tilde.mean()
    return theta


def generate_data_observed_rank(distrib_y, distrib_u, size = 1000):
    """
    generate_data:
        generate data following the specified distributions.
        Should be of class "rv_continuous" from scipy.stats
        
    :param distrib_y: distribution of Y, instance of rv_continuous
    :param distrib_u: distribution of U, instance of rv_continuous
    :param size: sample size for each vector
    """        
    y = distrib_y.ppf(np.random.uniform(size=size))  
    u = distrib_u.ppf(np.random.uniform(size=size))  
    theta0 = true_theta_observed_rank(distrib_y=distrib_y, distrib_u=distrib_u, size = 100000)
    
    return y, u, theta0


def performance_report(y_hat, theta0, n_obs, histograms=True, **kwargs):
    """
    performance_report:
        creates the report for simulations,
        computes bias, MSE, MAE and coverage rate.
        
    :param y_hat: B x K np.array of B simulations for K estimators
    :param theta0: scalar, true value of theta
    :param n_obs: sample size used during simulations.
    """
    sigma = kwargs.get('sigma', np.ones(y_hat.shape))
    file = kwargs.get('file', 'default_output_file')
    
    y_centered = y_hat - theta0
    report = {}
    report['theta0'] = theta0
    report['n_simu'] = len(y_hat)
    report['n_obs']  = n_obs
    report['bias']   = y_centered.mean(axis=0)
    report['MAE']    = abs(y_centered).mean(axis=0)
    report['RMSE']   = y_centered.std(axis=0)
    report['Coverage rate'] = (abs(y_centered/sigma) < norm.ppf(0.975)).mean(axis=0)
    report['Quantile .95'] = (np.sqrt(n_obs)*y_centered).quantile(q=.95, axis=0)
    report['CI size'] = 2*norm.ppf(0.975)*sigma.mean(axis=0)
    
    print('Theta_0: {:.2f}'.format(report['theta0']))
    print("Number of simulations: {} \n".format(report['n_simu']))
    print("Sample size: {} \n".format(report['n_obs']))
    for metric in ['bias', 'MAE', 'RMSE', 'Coverage rate', 'CI size', 'Quantile .95']:
        print(metric+': ')
        for model in y_centered.columns:
            print('- {}: {:.4f}'.format(model, report[metric][model]))
        print('\n')
        
    ##### WRITING TO FILE #####
    with open(file+'.txt', "a") as f:
        f.write('\n')
        f.write('Theta_0: {:.2f} \n'.format(report['theta0']))
        for metric in ['bias', 'MAE', 'RMSE', 'Coverage rate', 'CI size', 'Quantile .95']:
            f.write(metric+': \n')
            for model in y_centered.columns:
                f.write('- {}: {:.4f} \n'.format(model, report[metric][model]))
            f.write('\n')

    ##### SAVING HISTOGRAM #####
    if histograms:
        num_bins = 50
        for model in y_centered.columns:
            fig, ax = plt.subplots()
            n, bins, patches = ax.hist(np.sqrt(n_obs)*y_centered[model], num_bins, density=1)
            norm_fit = norm.pdf(bins, scale=np.sqrt(n_obs)*sigma[model].mean())
            ax.plot(bins, norm_fit, '--')
            ax.set_xlabel(r'$n^{1/2}$ ($\hat \theta$ - $\theta_0$)')
            ax.set_ylabel('Probability density')
            ax.set_title(r'Histogram for model: '+model)
            fig.tight_layout()
            plt.savefig(file+'_n='+str(n_obs)+'_'+model+'.jpg',dpi=(96))
    
    return report


def latex_table(results, file, models=['standard','smoothed', 'smoothed_lewbel-schennach'], digits=3):
    """
    latex_table:
        outputs a latex table from a list of results
    :param results: list of results based on the format results[sample_size][metric][model]
    :param file: name of the output file
    """
    metrics_set = ['bias', 'MAE', 'RMSE', 'Coverage rate', 'Quantile .95']

    k=0

    with open(file+'.tex', "a") as f:
        f.write('\n')
        f.write(r'\begin{table}')
        f.write('\n')

        for model in models:
            k += 1
            string = model
            item = 'model'
            sample_line = ' '
            header = r'\begin{tabular}{l|'
            for sample_size in results:
                sample_line = sample_line+ r' & \multicolumn{'+str(len(metrics_set))+'}{c}{'+str(sample_size)+'}'
                header = header + ('c'*len(metrics_set))
                for metric in metrics_set:
                    string = string+' & '+str(round(results[sample_size][metric][model], digits))
                    item = item+' & '+metric
            string = string +'\\\\'
            item = item +'\\\\'
            sample_line = sample_line +'\\\\'
            header = header + '}'
            ### WRITING
            if k == 1:
                f.write(header)
                f.write('\n')
                f.write(r'\toprule')
                f.write('\n')
                f.write(sample_line)
                f.write('\n')
                f.write(item)
                f.write('\n')
                f.write(r'\hline')
                f.write('\n')
            f.write(string)
            f.write('\n')
        
        f.write(r'\bottomrule')
        f.write('\n')
        f.write(r'\end{tabular}')
        f.write('\n')
        f.write(r'\end{table}')
        f.write('\n')

    return