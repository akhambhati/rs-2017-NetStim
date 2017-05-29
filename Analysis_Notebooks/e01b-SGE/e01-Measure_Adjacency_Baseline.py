#!/bin/zsh

#
# Make sure that output files arrive in the working directory
#$ -cwd
#
# Join the outputs together
#$ -j y
#
# Reserve 10 GB of memory
#$ -l h_vmem=3.5G,s_vmem=3.0G
#

source activate echobase
ipython -c "

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
sys.path.append('/data/jag/akhambhati/hoth_research/Echobase')
import Echobase

# Set Paths
path_CoreData = '/data/jag/akhambhati/Remotes/CORE.RAM_Stim'
path_PeriphData = '/home/akhambhati/Procd_Data/RSRCH.RAM_Stim'
path_ExpData = path_PeriphData + '/e01b-FuncNetw'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)
#### ---------------------- Front Matter ------------------------

# Grab the Task ID from QSUB
sge_task_id = int(os.environ['SGE_TASK_ID'])-1

# Load the file list
proc_list = pkl.load(open('{}/proc_list.pkl'.format(path_ExpData), 'r'))
pitem = proc_list[sge_task_id]

# Load data
df = h5py.File(pitem['raw_path'], 'r')
df_chan = io.loadmat(pitem['chan_path'])

# Make sure the good channel lists are correct
assert (df_chan['good_channels_jack'].shape[1] == df_chan['good_channels_ind'].shape[1])

# Retrieve data
evData = df['evData'][...]
fs = int(np.ceil(df['samp_freq'][0, 0]))
good_chan = np.array(map(int, df_chan['good_channels_ind'][0,:]-1))

# Handle electrodes
# Keep only good channels
evData = evData[:, good_chan]
n_win, n_chan = evData.shape

# Formulate output dictionary
adj = {'No_Stim': {}}

try:
    # Compute No-Stim Adjacency
    adj['No_Stim']['AlphaTheta'], adj['No_Stim']['Beta'], adj['No_Stim']['LowGamma'], adj['No_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[...], fs)

except:
    adj['No_Stim']['AlphaTheta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['No_Stim']['Beta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['No_Stim']['LowGamma'] = np.nan*np.zeros((n_chan, n_chan))
    adj['No_Stim']['HighGamma'] = np.nan*np.zeros((n_chan, n_chan))

# Save the output
np.savez(pitem['res_path'], adj=adj)
"
