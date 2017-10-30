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
path_CoreData = '/data/jag/bassett-lab/akhambhati/CORE.PS_Stim'
path_PeriphData = '/data/jag/bassett-lab/akhambhati/RSRCH.PS_Stim'
path_ExpData = path_PeriphData + '/e02-FuncNetw.Bipolar.Stim'

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
    df_chan = io.loadmat('{}/Electrode_Info/{}.mat'.format(path_CoreData, subj_id))
    df_event = io.loadmat('{}/Event_Table/{}_events.mat'.format(path_CoreData, subj_id))
except:
    print('Could not load raw, electrode, or event file for {}'.format(subj_id))
    sys.exit()

# Retrieve data
evData = df_raw['evData'][...]
fs = int(np.ceil(df_raw['Fs'][0, 0]))
n_chan, n_samp = evData.shape

# Retrieve event and relevant information
event = df_event['events'][0, int(event_id)-1]

if not (event['type'][0] in ['STIMULATING', 'SHAM']):
    print('Invalid Event Type: {}'.format(event['type'][0]))
    sys.exit()

if event['type'][0] == 'STIMULATING':
    stim_duration = event['pulse_duration'][0, 0] / 1000.0

if event['type'][0] == 'SHAM':
    event_stim_ix = np.flatnonzero(df_event['events']['type'][0, :] == 'STIMULATING')
    closest_event = np.argmin(np.abs(event_stim_ix - (int(event_id)-1)))
    stim_duration = df_event['events'][0, closest_event]['pulse_duration'][0, 0] / 1000.0

# Handle electrodes
chan_bp_id = np.array(sorted(df_chan['electrode_id_bp'].tolist(), key=lambda x: (x[0], x[1])))
n_chan_bp = chan_bp_id.shape[0]
evData_bp = np.zeros((n_chan_bp, n_samp))

for chan_bp_ix, chan_bp in enumerate(chan_bp_id):
    anode_ix = np.flatnonzero(df_chan['electrode_id'][0, :] == chan_bp[0])[0]
    cathode_ix = np.flatnonzero(df_chan['electrode_id'][0, :] == chan_bp[1])[0]

    evData_bp[chan_bp_ix, :] = evData[anode_ix, :] - evData[cathode_ix, :]
evData_bp = evData_bp.T

# Window the stimulation clip
n_win_dur = int(0.5*fs)

n_stim_start = int(0.5*fs)
n_stim_dur = int(stim_duration*fs)
n_stim_end = n_stim_start + n_stim_dur
n_stim_pad = int(25/1000.0*fs)

win_pre_stim = list(np.arange(n_stim_start-n_win_dur, n_stim_start))
win_post_stim = list(np.arange(n_stim_end+n_stim_pad, n_stim_end+n_stim_pad+n_win_dur))

# Formulate output dictionary
adj = {'Pre_Stim': {}, 'Post_Stim': {}}

# Compute Pre-Stim Adjacency
adj['Pre_Stim']['AlphaTheta'], adj['Pre_Stim']['Beta'], adj['Pre_Stim']['LowGamma'], adj['Pre_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData_bp[win_pre_stim, :], fs, avgref=False)

# Compute Pre-Stim Adjacency
adj['Post_Stim']['AlphaTheta'], adj['Post_Stim']['Beta'], adj['Post_Stim']['LowGamma'], adj['Post_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData_bp[win_post_stim, :], fs, avgref=False)

# Save the output
np.savez(foutput, adj=adj)
"
