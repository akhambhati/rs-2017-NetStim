#### ---------------------- Front Matter ------------------------

# Standard I/O imports
import os
import sys
import glob
import pickle as pkl
import h5py
import scipy.io as io

# Data manipulation imports
import numpy as np
#sys.path.append('/data/jag/akhambhati/hoth_research/Echobase')
sys.path.append('/Users/akhambhati/Developer/hoth_research/Echobase')
import Echobase

# Set Paths
path_CoreData = '/Users/akhambhati/Remotes/CORE.PS_Stim'
path_PeriphData = '/Users/akhambhati/Remotes/RSRCH.PS_Stim'
path_ExpData = path_PeriphData + '/e02-FuncNetw.Bipolar.Baseline'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)
#### ---------------------- Front Matter ------------------------

raw_path = glob.glob('{}/Base_Trials/*.mat'.format(path_CoreData))
pkl.dump(raw_path, open('{}/proc_list.pkl'.format(path_ExpData), 'w'))
