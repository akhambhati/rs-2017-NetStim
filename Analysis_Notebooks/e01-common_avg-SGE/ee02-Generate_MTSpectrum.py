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
path_ExpData = path_PeriphData + '/e01-MTSpectrum.CommonAverage.Stim'

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
foutput = '{}/MTSpectrum.{}.npz'.format(path_ExpData, base_id)
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

stim_anode_jack = event['stimAnode'][0, 0]
stim_cathode_jack = event['stimCathode'][0, 0]

# Handle electrodes
chan_bp_id = np.array(sorted(df_chan['electrode_id_bp'].tolist(), key=lambda x: (x[0], x[1])))
chan_mp_id = np.unique(chan_bp_id.reshape(-1))
chan_mp_id = np.setdiff1d(chan_mp_id, [stim_anode_jack, stim_cathode_jack])
n_chan_mp = chan_mp_id.shape[0]
evData_mp = np.zeros((n_chan_mp, n_samp))

for chan_mp_ix, chan_mp in enumerate(chan_mp_id):
    anode_ix = np.flatnonzero(df_chan['electrode_id'][0, :] == chan_mp)[0]

    evData_mp[chan_mp_ix, :] = evData[anode_ix, :]
evData_mp = evData_mp.T

# Window the stimulation clip
n_win_dur = int(0.5*fs)

n_stim_start = int(0.5*fs)
n_stim_dur = int(stim_duration*fs)
n_stim_end = n_stim_start + n_stim_dur
n_stim_pad = int(25/1000.0*fs)

win_pre_stim = list(np.arange(n_stim_start-n_win_dur, n_stim_start))
win_post_stim = list(np.arange(n_stim_end+n_stim_pad, n_stim_end+n_stim_pad+n_win_dur))

# Formulate output dictionary
mtspectrum = {'Pre_Stim': {}, 'Post_Stim': {}}

# Compute Pre-Stim multitaper spectrum
mtspectrum['Pre_Stim']['freq'], mtspectrum['Pre_Stim']['psd'] = Echobase.Pipelines.ecog_powerspec.multiband(evData_mp[win_pre_stim, :], fs, avgref=True)

# Compute Post-Stim multitaper spectrum
mtspectrum['Post_Stim']['freq'], mtspectrum['Post_Stim']['psd'] = Echobase.Pipelines.ecog_powerspec.multiband(evData_mp[win_post_stim, :], fs, avgref=True)

# Save the output
np.savez(foutput, mtspectrum=mtspectrum)
"
