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
    event = df_event['events'][0, :]
    duration_distr = np.array([dur[0,0] for dur in event['pulse_duration']])
    duration_distr = np.unique(duration_distr)
    duration_distr = duration_distr[duration_distr > 0]

    # Retrieve data
    evData = df_raw['evData'][...][df_monop['monopolar_resort_ix'], :].T
    fs = int(np.ceil(df_raw['Fs'][0, 0]))
    n_samp, n_chan = evData.shape

    # Formulate output dictionary
    adj = {}

    # Remove artifactual channels for this stim location
    for stim_pair_tag in df_monop['monopolar_id_artifact'][()].keys():
        adj[stim_pair_tag] = {}

        stim_pair_lbl = stim_pair_tag.split('_')
        nonstim_lbl_artifact = np.unique(np.setdiff1d(
            df_monop['monopolar_lbl_artifact'][()][stim_pair_tag],
            stim_pair_lbl))
        nonstim_artifact_ix = np.array([np.flatnonzero(
            df_monop['monopolar_lbl'] == lbl)[0]
            for lbl in nonstim_lbl_artifact])
        goodchan_ix = np.setdiff1d(np.arange(n_chan), nonstim_artifact_ix)

        evData_good = evData[:, goodchan_ix]

        # Iterate over the possible stim durations
        for stim_dur in duration_distr:
            adj[stim_pair_tag][stim_dur] = []

            # Window the baseline clip
            n_win_dur = int(0.5*fs)
            n_stim_dur = int((stim_dur/1000.0)*fs)
            n_stim_end = n_win_dur + n_stim_dur
            n_stim_pad = int(100/1000.0*fs)

            n_win_block = n_win_dur + n_stim_dur + n_stim_pad + n_win_dur
            n_block = int(np.floor(n_samp / n_win_block))

            for block_ix in xrange(n_block):
                start_ix = block_ix*n_win_block
                win_pre_stim = list(np.arange(start_ix, start_ix+n_win_dur))
                win_post_stim_1= list(np.arange(start_ix+n_stim_end+n_stim_pad,
                                                start_ix+n_stim_end+n_stim_pad+n_win_dur))
                win_post_stim_2= list(np.arange(start_ix+n_stim_end+n_stim_pad+n_win_dur,
                                                start_ix+n_stim_end+n_stim_pad+2*n_win_dur))


                # Formulate output dictionary for this block
                adj_temp = {'Pre_Stim': {}, 'Post_Stim_1': {}, 'Post_Stim_2': {}}

                # Compute Pre-Stim adjacency
                if (np.min(win_pre_stim) >= 0) & (np.max(win_pre_stim) < n_samp):
                    adj_temp['Pre_Stim']['AlphaTheta'], adj_temp['Pre_Stim']['Beta'], adj_temp['Pre_Stim']['LowGamma'], adj_temp['Pre_Stim']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData_good[win_pre_stim, :], fs, avgref=True)
                else:
                    adj_temp['Pre_Stim'] = []

                # Compute Post-Stim adjacency
                if (np.min(win_post_stim_1) >= 0) & (np.max(win_post_stim_1) < n_samp):
                    adj_temp['Post_Stim_1']['AlphaTheta'], adj_temp['Post_Stim_1']['Beta'], adj_temp['Post_Stim_1']['LowGamma'], adj_temp['Post_Stim_1']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData_good[win_post_stim_1, :], fs, avgref=True)
                else:
                    adj_temp['Post_Stim_1'] = []

                # Compute Post-Stim adjacency
                if (np.min(win_post_stim_2) >= 0) & (np.max(win_post_stim_2) < n_samp):
                    adj_temp['Post_Stim_2']['AlphaTheta'], adj_temp['Post_Stim_2']['Beta'], adj_temp['Post_Stim_2']['LowGamma'], adj_temp['Post_Stim_2']['HighGamma'] = Echobase.Pipelines.ecog_network.multiband_conn(evData_good[win_post_stim_2, :], fs, avgref=True)
                else:
                    adj_temp['Post_Stim_2'] = []


                adj[stim_pair_tag][stim_dur].append(adj_temp)

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
