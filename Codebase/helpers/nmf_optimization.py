from __future__ import division

import numpy as np

from ..Common.display import my_display
from ..Networks.SubgraphDetection.nonnegfac import nmf

def execute(expr_id, path_cfg_matr, param_id, param_alpha, param_beta, param_rank, path_output):
    # Cast appropriate data types
    expr_id = str(expr_id)
    path_cfg_matr = str(path_cfg_matr)
    param_id = int(param_id)
    param_alpha = float(param_alpha)
    param_beta = float(param_beta)
    param_rank = int(param_rank)
    path_output = str(param_output)

    # Begin function
    my_display("\n -- Processing: {} -- Parameter: {}".format(expr_id, param_id), True)

    df = np.load(path_cfg_matr)

    cfg_matr = np.nan_to_num(df['cfg_matr'])

    # Initialize the factors for NMF
    fac_subnet = np.random.uniform(low=0, high=1.0,
                                   size=(param_rank,
                                         cfg_matr.shape[1]))
    fac_coef = np.random.uniform(low=0, high=1.0,
                                 size=(param_rank,
                                       cfg_matr.shape[0]))

    # Run NMF Algorithm
    fac_subnet, fac_coef, err = nmf.snmf_bcd(
        cfg_matr,
        alpha=param_alpha, beta=param_beta,
        fac_subnet_init=fac_subnet,
        fac_coef_init=fac_coef,
        max_iter=100, verbose=False)

    # Cache the NMF result
    np.savez("{}/NMF_Optimization.Param_{}.{}.npz".format(path_output, param_id, expr_id),
             fac_subnet=fac_subnet, fac_coef=fac_coef, err=err)
