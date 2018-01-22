#### ---------------------- Front Matter ------------------------
# Standard I/O imports
import os
import sys
import glob
import pickle as pkl
import h5py
import scipy.io as io

# Set Paths
#location = 'Hoth'
location = 'cfn'

if location == 'Hoth':
    sys.path.append('/Users/akhambhati/Developer/hoth_research/Echobase')
    sys.path.append('/Users/akhambhati/Developer/hoth_research/rs-Net_Stim/Analysis_Notebooks/e00-screen_channels')        
    path_CoreData = '/Users/akhambhati/Remotes/CORE.PS_Stim'
    path_PeriphData = '/Users/akhambhati/Remotes/RSRCH.PS_Stim'
elif location == 'cfn':
    sys.path.append('/data/jag/akhambhati/hoth_research/Echobase')
    sys.path.append('/data/jag/akhambhati/hoth_research/rs-Net_Stim/Analysis_Notebooks/e00-screen_channels')            
    path_CoreData = '/data/jag/bassett-lab/akhambhati/CORE.PS_Stim'
    path_PeriphData = '/data/jag/bassett-lab/akhambhati/RSRCH.PS_Stim'
else:
    raise Exception('Invalid location specified')
path_ExpData = path_PeriphData + '/e02-FuncNetw.CommonAverage.Baseline'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)

# Data manipulation imports
import numpy as np
import Echobase
import handle_bad_channels
#### ---------------------- Front Matter ------------------------

raw_path = glob.glob('{}/Base_Trials/*.mat'.format(path_CoreData))
pkl.dump(raw_path, open('{}/proc_list.pkl'.format(path_ExpData), 'w'))
