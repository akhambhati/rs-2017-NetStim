from __future__ import division
from IPython.display import display

import os
import sys
import glob
import json
import subprocess

import numpy as np
import pandas as pd
import seaborn as sns
import scipy.io as io
import h5py
import matplotlib.pyplot as plt
from matplotlib import rcParams

import fig_plotting
rcParams = fig_plotting.update_rcparams(rcParams)

import scipy.stats as stats

os.chdir('../')
import Codebase
conv_adj_matr_to_cfg_matr = Codebase.Networks.configuration.convert_adj_matr_to_cfg_matr
conv_cfg_vec_to_adj_matr = Codebase.Networks.configuration.convert_conn_vec_to_adj_matr
os.chdir('./Analysis Notebooks/')

path_CoreData = '/home/akhambhati/JagHome/hoth_research/CoreData/Sync_Cog_Control-Medaglia'
path_PeriphData = '/home/akhambhati/JagHome/hoth_research/PeriphData/ds-NMF_CogControl'
path_InpData = path_PeriphData + '/e01-FuncNetw'
path_ExpData = path_PeriphData + '/e02-FuncSubg'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)


from Codebase.Networks.SubgraphDetection.nonnegfac import nmf

path_cfg_matr = glob.glob('{}/NMF_Optimization.CfgMatr.npz'.format(path_ExpData))[0]
seed_path = glob.glob('{}/NMF_Optimized.Seed_*.npz'.format(path_ExpData))
n_seed_block = 100
seed_path_blocks = np.random.permutation(seed_path).reshape(-1, n_seed_block)

for block_ix, seed_path_block in enumerate(seed_path_blocks):
    print('Processing Block: {}'.format(block_ix+1))

    # Concatenate subgraphs from block seeds
    fac_subnet_seeds = []
    for path_block in seed_path_block:
        data = np.load(path_block, mmap_mode='r')
        fac_subnet = data['fac_subnet'][:, :]
        data.close()

        n_fac = fac_subnet.shape[0]
        n_conn = fac_subnet.shape[1]

        for fac_ix in xrange(n_fac):
            fac_subnet_seeds.append(fac_subnet[fac_ix, :])
    fac_subnet_seeds = np.array(fac_subnet_seeds)

    n_obs = fac_subnet_seeds.shape[0]
    n_conn = fac_subnet_seeds.shape[1]

    if block_ix == 0:
        fac_subnet_init = np.random.uniform(low=0.0, high=1.0, size=(n_fac, n_conn))
    else:
        fac_subnet_init = fac_cons_subnet
    fac_coef_init = np.random.uniform(low=0.0, high=1.0, size=(n_fac, n_obs))

    # Consensus Subgraphs
    fac_cons_subnet, fac_cons_seeds, err = nmf.snmf_bcd(
        fac_subnet_seeds,
        alpha=0.0,
        beta=0.0,
        fac_subnet_init=fac_subnet_init,
        fac_coef_init=fac_coef_init,
        max_iter=100, verbose=True)

# Consensus Coefficients
data_cfg = np.load(path_cfg_matr, mmap_mode='r')
cfg_matr = np.nan_to_num(data_cfg['cfg_matr'][:, :])
n_win = cfg_matr.shape[0]
fac_cons_subnet_2, fac_cons_coef_2, err = nmf.snmf_bcd(
    cfg_matr,
    alpha=0.0,
    beta=0.0,
    fac_subnet_init=fac_cons_subnet,
    fac_coef_init=np.random.uniform(low=0.0, high=1.0, size=(n_fac, n_win)),
    max_iter=100, verbose=True)

# Cache the Consensus NMF result
np.savez("{}/NMF_Consensus.npz".format(path_ExpData),
         fac_subnet=fac_cons_subnet_2, fac_coef=fac_cons_coef_2, err=err)
