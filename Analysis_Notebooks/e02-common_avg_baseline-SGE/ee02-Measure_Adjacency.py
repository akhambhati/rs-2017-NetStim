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

# Set Paths
#location = 'Hoth'
location = 'cfn'

if location == 'Hoth':
    sys.path.append('/Users/akhambhati/Developer/hoth_research/Echobase')
    path_CoreData = '/Users/akhambhati/Remotes/CORE.PS_Stim'
    path_PeriphData = '/Users/akhambhati/Remotes/RSRCH.PS_Stim'
elif location == 'cfn':
    sys.path.append('/data/jag/akhambhati/hoth_research/Echobase')
    path_CoreData = '/data/jag/bassett-lab/akhambhati/CORE.PS_Stim'
    path_PeriphData = '/data/jag/bassett-lab/akhambhati/RSRCH.PS_Stim'
else:
    raise Exception('Invalid location specified')
path_InpData = path_PeriphData + '/e00-Clean_Channels'
path_ExpData = path_PeriphData + '/e02-FuncNetw.CommonAverage.Baseline'

for path in [path_CoreData, path_PeriphData, path_InpData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)

# Data manipulation imports
import numpy as np
import Echobase
#### ---------------------- Front Matter ------------------------

# Grab the Task ID from QSUB
sge_task_id = int(os.environ['SGE_TASK_ID'])-1

# Load the file list
proc_list = pkl.load(open('{}/proc_list.pkl'.format(path_ExpData), 'r'))
pitem = proc_list[sge_task_id]

# Parse the pitem path
base_id = '.'.join(pitem.split('/')[-1].split('.')[:-1])
subj_id = pitem.split('/')[-1].split('.')[0]
event_id = pitem.split('/')[-1].split('.')[-2]

# Set output
foutput = '{}/Adjacency.{}.npz'.format(path_ExpData, base_id)
if os.path.exists(foutput):
    print('Output file already exists: {}'.format(foutput))
    sys.exit()

# Load data
try:
    df_raw = io.loadmat(pitem)
    df_monop = np.load('{}/Clean_Channels.{}.npz'.format(path_InpData, subj_id))
except:
    print('Could not load raw, electrode, or event file for {}'.format(subj_id))
    sys.exit()

# Retrieve data
evData = df_raw['evData'][...][df_monop['monopolar_resort_ix'], :].T
fs = int(np.ceil(df_raw['Fs'][0, 0]))
n_samp, n_chan = evData.shape

# Window the baseline clip
n_win_dur = int(0.5*fs)
n_win = int(np.floor(n_samp / n_win_dur))

# Formulate output dictionary
adj = {'AlphaTheta': [],
       'Beta': [],
       'LowGamma': [],
       'HighGamma': []}

for win_ix in xrange(n_win):
    clip_ix = np.arange(win_ix*n_win_dur, (win_ix+1)*n_win_dur)
    adj_AlphaTheta, adj_Beta, adj_LowGamma, adj_HighGamma = Echobase.Pipelines.ecog_network.multiband_conn(evData_mp[clip_ix, :], fs, avgref=True)

    adj['AlphaTheta'].append(adj_AlphaTheta)
    adj['Beta'].append(adj_Beta)
    adj['LowGamma'].append(adj_LowGamma)
    adj['HighGamma'].append(adj_HighGamma)

# Save the output
np.savez(foutput, adj=adj)
"
