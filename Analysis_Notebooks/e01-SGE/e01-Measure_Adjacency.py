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
path_ExpData = path_PeriphData + '/e01-FuncNetw'

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
df_event = io.loadmat(pitem['event_path'])
df_lut = h5py.File(pitem['trial_lut_path'], 'r')
trial_id = int(pitem['trial_id'])

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

# Find event in LUT
event_ind = df_lut['trial_lut'][1,:][df_lut['trial_lut'][0,:] == trial_id]
assert len(event_ind) == 1
event_ind = int(event_ind[0] - 1)

# Get Stim Electrode Jacksheet label
stim_anode_jack = df_event['events'][0, event_ind]['stimAnode'][0,0]
stim_cathode_jack = df_event['events'][0, event_ind]['stimCathode'][0,0]
stim_anode_ix = np.flatnonzero(df_chan['good_channels_jack'][0,:] == stim_anode_jack)[0]
stim_cathode_ix = np.flatnonzero(df_chan['good_channels_jack'][0,:] == stim_cathode_jack)[0]

# Remove stim electrodes from network
all_chan_ix = np.arange(n_chan)
evData = evData[:, list(np.setdiff1d(all_chan_ix, [stim_anode_ix, stim_cathode_ix]))]

# Window the stimulation clip
stim_dur = df_event['events'][0, event_ind]['pulse_duration'][0,0]
n_win_dur = int(1*fs/2)

n_stim_start = int(1*fs)
n_stim_dur = int(stim_dur/1000.0*fs)
n_stim_end = n_stim_start + n_stim_dur
n_stim_pad = int(25/1000.0*fs)

win_pre_stim = list(np.arange(n_stim_start-n_win_dur, n_stim_start))
win_post_stim = list(np.arange(n_stim_end+n_stim_pad, n_stim_end+n_stim_pad+n_win_dur))

#win_pre_stim_old = list(np.arange(fs-fs/2-1, fs-1))
#win_post_stim_old = list(np.arange(fs+fs+1, len(evData)))

#print('Pre_Stim_Old: {}, {}'.format(np.min(win_pre_stim_old), np.max(win_pre_stim_old)))
#print('Pre_Stim_New: {}, {}'.format(np.min(win_pre_stim), np.max(win_pre_stim)))
#print('Post_Stim_Old: {}, {}'.format(np.min(win_post_stim_old), np.max(win_post_stim_old)))
#print('Post_Stim_New: {}, {}'.format(np.min(win_post_stim), np.max(win_post_stim)))


# Formulate output dictionary
adj = {'Pre_Stim': {}, 'Post_Stim': {}}

try:
    # Compute Pre-Stim Adjacency
    adj['Pre_Stim']['AlphaTheta'], adj['Pre_Stim']['Beta'], adj['Pre_Stim']['LowGamma'], adj['Pre_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[win_pre_stim, :], fs)

    # Compute Pre-Stim Adjacency
    adj['Post_Stim']['AlphaTheta'], adj['Post_Stim']['Beta'], adj['Post_Stim']['LowGamma'], adj['Post_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[win_post_stim, :], fs)
except:
    adj['Pre_Stim']['AlphaTheta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Pre_Stim']['Beta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Pre_Stim']['LowGamma'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Pre_Stim']['HighGamma'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Post_Stim']['AlphaTheta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Post_Stim']['Beta'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Post_Stim']['LowGamma'] = np.nan*np.zeros((n_chan, n_chan))
    adj['Post_Stim']['HighGamma'] = np.nan*np.zeros((n_chan, n_chan))

# Save the output
np.savez(pitem['res_path'], adj=adj)
"
