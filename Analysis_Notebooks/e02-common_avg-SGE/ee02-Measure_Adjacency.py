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
path_ExpData = path_PeriphData + '/e02-FuncNetw.CommonAverage.Stim'

for path in [path_CoreData, path_PeriphData, path_InpData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)

# Data manipulation imports
import numpy as np
import Echobase
#### ---------------------- Front Matter ------------------------


def run(pitem):

    # Parse the pitem path
    subj_id = pitem.split('/')[-1].split('.')[0]
    event_id = pitem.split('/')[-1].split('.')[-2]

    # Load data
    try:
        df_raw = io.loadmat(pitem)
        df_event = io.loadmat('{}/Event_Table/{}_events.mat'.format(path_CoreData, subj_id))
        df_monop = np.load('{}/Clean_Channels.{}.npz'.format(path_InpData, subj_id))
    except:
        print('Could not load raw, electrode, or event file for {}'.format(subj_id))
        sys.exit()

    # Get event data
    event = df_event['events'][0, int(event_id)-1]
    if event['type'][0] == 'STIMULATING':
        stim_duration = event['pulse_duration'][0, 0] / 1000.0
    elif event['type'][0] == 'SHAM':
        event_stim_ix = np.flatnonzero(df_event['events']['type'][0, :] == 'STIMULATING')
        closest_event = np.argmin(np.abs(event_stim_ix - (int(event_id)-1)))
        stim_duration = df_event['events'][0, closest_event]['pulse_duration'][0, 0] / 1000.0
    else:
        print('Invalid Event Type: {}'.format(event['type'][0]))
        sys.exit()

    stim_anode_tag = event['stimAnodeTag'][0]
    stim_cathode_tag = event['stimCathodeTag'][0]
    stim_pair_tag = '_'.join({stim_anode_tag, stim_cathode_tag})

    # Retrieve data
    evData = df_raw['evData'][...][df_monop['monopolar_resort_ix'], :].T
    fs = int(np.ceil(df_raw['Fs'][0, 0]))
    n_samp, n_chan = evData.shape

    # Remove artifactual channels for this stim location
    goodchan_ix = np.setdiff1d(np.arange(n_chan), df_monop['monopolar_id_artifact'][()][stim_pair_tag])
    evData = evData[:, goodchan_ix]

    # Window the stimulation clip
    n_win_dur = int(0.5*fs)

    n_stim_start = int(0.5*fs)
    n_stim_dur = int(stim_duration*fs)
    n_stim_end = n_stim_start + n_stim_dur
    n_stim_pad = int(100/1000.0*fs)

    win_pre_stim = list(np.arange(n_stim_start-n_win_dur, n_stim_start))
    win_post_stim_1 = list(np.arange(n_stim_end+n_stim_pad, n_stim_end+n_stim_pad+n_win_dur))
    win_post_stim_2 = list(np.arange(n_stim_end+n_stim_pad+n_win_dur, n_stim_end+n_stim_pad+2*n_win_dur))

    # Formulate output dictionary
    adj = {'Pre_Stim': {}, 'Post_Stim_1': {}, 'Post_Stim_2': {}}

    # Compute Pre-Stim Adjacency
    adj['Pre_Stim']['AlphaTheta'], adj['Pre_Stim']['Beta'], adj['Pre_Stim']['LowGamma'], adj['Pre_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[win_pre_stim, :], fs, avgref=True)

    # Compute Pre-Stim Adjacency
    adj['Post_Stim_1']['AlphaTheta'], adj['Post_Stim_1']['Beta'], adj['Post_Stim_1']['LowGamma'], adj['Post_Stim_1']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[win_post_stim_1, :], fs, avgref=True)
    adj['Post_Stim_2']['AlphaTheta'], adj['Post_Stim_2']['Beta'], adj['Post_Stim_2']['LowGamma'], adj['Post_Stim_2']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData[win_post_stim_2, :], fs, avgref=True)

    return adj


if __name__ == '__main__':
    # Grab the Task ID from QSUB
    sge_task_id = int(os.environ['SGE_TASK_ID'])-1

    # Load the file list
    proc_list = pkl.load(open('{}/proc_list.pkl'.format(path_ExpData), 'r'))
    pitem = proc_list[sge_task_id]

    # Parse the pitem path
    base_id = '.'.join(pitem.split('/')[-1].split('.')[:-1])

    # Set output
    foutput = '{}/Adjacency.{}.npz'.format(path_ExpData, base_id)
    if os.path.exists(foutput):
        print('Output file already exists: {}'.format(foutput))
        sys.exit()

    adj = run(pitem)

    # Save the output
    np.savez(foutput, adj=adj)
"
