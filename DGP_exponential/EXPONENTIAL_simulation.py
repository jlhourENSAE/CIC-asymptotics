#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main file to run simulations.

Currently:
    - Y ~ Pareto,
    - Z ~ Exponential,
    - X ~ Exponential.
    
Created on Mon Nov  9 12:07:05 2020

@author: jeremylhour
"""

import sys, os
sys.path.append(os.path.join(os.getcwd(),'functions/'))

import numpy as np
import pandas as pd
import random
import time
import yaml
import math
import pickle

from statsmodels.distributions.empirical_distribution import ECDF

from func_main import estimator_unknown_ranks
from func_ecdf import smoothed_ecdf
from func_simu import analytical_theta, generate_data, performance_report 
from func_kde import kernel_density_estimator, gaussian_kernel, epanechnikov_kernel

from scipy.stats import expon, pareto
   

########## SETTING UP FOLDER IF NEEDED ##########
if not os.path.exists('output'):
    os.makedirs('output')

if not os.path.exists('output/raw'):
    os.makedirs('output/raw')
    

########## LOAD YAML CONFIG ##########
#config_file= os.path.join(os.getcwd(),'example_config_simulation.yml')
config_file= os.path.join(os.getcwd(),sys.argv[1])

with open(config_file, 'r') as stream:
    config = yaml.safe_load(stream)
    
B = config['nb_simu']

lambda_x = config['lambda_x']
lambda_z = config['lambda_z']
alpha_y = config['alpha_y']

    
print(f'lambda_x={lambda_x} -- lambda_z={lambda_z} -- alpha_y={alpha_y}',
      f'Parameter values give b_2={round(1-lambda_x/lambda_z, 2)}',
      f'Parameter values give d_2={round(1/alpha_y, 2)}',
      f'So b_2+d_2={round(1-lambda_x/lambda_z+1/alpha_y, 2)}',
      '--- Remember, b_2 + d_2 should be below .5 for Theorem 2 to apply',
      '--- and below 1 for theta_0 to be finite.',
      sep = '\n'
      )


##### SAVING TO FILE ###########
outfile = 'output/simulations_B='+str(B)+'_lambda_x='+str(lambda_x)+'_lambda_z='+str(lambda_z)+'_alpha_y='+str(alpha_y)
    
with open(outfile+'.txt', "a") as f:
    f.write('\n')
    f.write('lambda_x={:.2f} -- lambda_z={:.2f} -- alpha_y={:.2f} \n'.format(lambda_x, lambda_z, alpha_y),)
    f.write('Parameter values give b_2={:.2f} \n'.format(1-lambda_x/lambda_z))
    f.write('Parameter values give d_2={:.2f} \n'.format(1/alpha_y))
    f.write('So b_2+d_2={:.2f} \n'.format(1-lambda_x/lambda_z+1/alpha_y))
    f.write('\n')


########## CORE CODE ##########
nb_estimators = 5
sample_size_set = config['sample_size']
big_results = {}

for sample_size in sample_size_set:
    print('Running {} simulations with sample size {}...'.format(B, sample_size))
    with open(outfile+'.txt', "a") as f:
        f.write('Running {} simulations with sample size {}...'.format(B, sample_size))

    random.seed(999)

    results = np.zeros(shape=(B, nb_estimators))
    sigma = np.zeros(shape=(B, nb_estimators))

    start_time = time.time()

    for b in range(B):
        sys.stdout.write("\r{0}".format(b))
        sys.stdout.flush()
        
        y, z, x =  generate_data(distrib_y = pareto(b=alpha_y, loc=-1),
                                 distrib_z = expon(scale=1/lambda_z),
                                 distrib_x = expon(scale=1/lambda_x),
                                 size = sample_size)
        # Estimator and standard error
        theta_standard, sigma_standard = estimator_unknown_ranks(y, x, z, method="standard")
        theta_standard_x, sigma_standard_x = estimator_unknown_ranks(y, x, z, method="standard", se_method="xavier")
        
        theta_smooth, sigma_smooth = estimator_unknown_ranks(y, x, z, method="smoothed", se_method="kernel")
        theta_ls, sigma_ls = estimator_unknown_ranks(y, x, z, method="smoothed", se_method="lewbel-schennach")
        theta_x, sigma_x = estimator_unknown_ranks(y, x, z, method="smoothed", se_method="xavier")

        # Collecting results
        results[b,] = [theta_standard, theta_standard_x, theta_smooth, theta_ls, theta_x]
        sigma[b,] = [sigma_standard, sigma_standard_x, sigma_smooth, sigma_ls, sigma_x]
    
        # Checking division error
        if math.isinf(sigma_smooth) or np.isnan(sigma_ls):
            print(' -- error for this iteration')
            results[b,] = [np.nan]*nb_estimators
            sigma[b,] = [np.nan]*nb_estimators

    print(f"Temps d'exécution total : {(time.time() - start_time):.2f} secondes ---")

    ########## POST-PROCESSS ##########
    results = pd.DataFrame(results)
    results.dropna(axis=0, inplace=True)
    
    sigma = pd.DataFrame(sigma)
    sigma.dropna(axis=0, inplace=True)
    
    theta0 = analytical_theta(alpha_y = alpha_y, lambda_z = lambda_z, lambda_x = lambda_x)
    
    y_hat = pd.DataFrame({'standard_kernel': results[0],
                          'standard_xavier': results[1],
                          'smooth_kernel': results[2],
                          'smooth_ls': results[3],
                          'smooth_xavier': results[4]})
    
    sigma_df = pd.DataFrame({'standard_kernel': sigma[0],
                             'standard_xavier': sigma[1],
                             'smooth_kernel': sigma[2],
                             'smooth_ls': sigma[3],
                             'smooth_xavier': sigma[4]})
    
    report = performance_report(y_hat, theta0, n_obs=sample_size, sigma=sigma_df, file=outfile)
    big_results[sample_size] = report
    
    
########## SAVING RESULTS OBJECT ##########
pickle_file = 'output/raw/simulations_B='+str(B)+'_lambda_x='+str(lambda_x)+'_lambda_z='+str(lambda_z)+'_alpha_y='+str(alpha_y)
pickle.dump(big_results, open(pickle_file+'.p','wb'))