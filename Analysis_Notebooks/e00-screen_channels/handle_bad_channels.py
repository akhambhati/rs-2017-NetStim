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
path_ExpData = path_PeriphData + '/e00-Clean_Channels'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)

# Data manipulation imports
import numpy as np
import scipy.stats as stats
import Echobase
#### ---------------------- Front Matter ------------------------

alpha = 0.05


def find_index_in_list(ref_list, itm_list):
    ix_list = []
    for itm in itm_list:
        ix = np.flatnonzero(ref_list == itm)
        if not (len(ix) == 1):
            continue
        ix_list.append(ix[0])
    ix_list = np.array(ix_list)
    return ix_list


def init_channels(subject_id):
    df_chan = io.loadmat('{}/Electrode_Info/{}.mat'.format(path_CoreData, subject_id))

    # Get the bipolar electrode list and convert it to a monopolar list
    if not (df_chan['electrode_id_bp'].shape == df_chan['electrode_label_bp'].shape):
        raise Exception('Bipolar IDs and Bipolar Labels are mismatched.')
    chan_mp_id, unique_ix = np.unique(df_chan['electrode_id_bp'].reshape(-1), return_index=True)
    chan_mp_lbl = np.array([ee[0] for ee in df_chan['electrode_label_bp'].reshape(-1)])[unique_ix]
    n_chan_mp = len(chan_mp_id)

    # Screen visually-identified bad channels
    chan_mp_id = np.intersect1d(chan_mp_id, df_chan['electrode_good'][:, 0])

    # Re-sort electrodes in order of chan_mp_id
    if len(np.setdiff1d(chan_mp_id, df_chan['electrode_id'][0, :])) > 0:
        raise Exception('Monopolar list contains IDs not in master electrode list.')
    resort_ix = find_index_in_list(df_chan['electrode_id'][0, :], chan_mp_id)

    return chan_mp_id, chan_mp_lbl, resort_ix


def find_stim_artifact(subject_id):
    df_event = io.loadmat('{}/Event_Table/{}_events.mat'.format(path_CoreData, subject_id))

    # Get unique stim anode/cathode pairs
    stim_pair_tag = np.unique([set([ev['stimAnodeTag'][0], ev['stimCathodeTag'][0]])
                                 for ev in df_event['events'][0]])

    # Screen stimulation-related electrodes
    chan_mp_id, chan_mp_lbl, resort_ix = init_channels(subject_id)

    chan_artifact_ix = {}
    for pair_tag in stim_pair_tag:
        pair_tag_key = '_'.join(pair_tag)
        chan_artifact_ix[pair_tag_key] = []

        # First, add the stimulated electrodes
        for tag in list(pair_tag):
            chan_artifact_ix[pair_tag_key].append(tag)

        # Next, compute features related to stim artifact
        pre_stim_mean_amp = []
        post_stim_mean_amp = []
        for ev_id, ev in enumerate(df_event['events'][0]):

            # Check that the event fits criteria
            if not ev['type'][0] in ['STIMULATING']:
                continue

            ev_pair_tag = {ev['stimAnodeTag'][0], ev['stimCathodeTag'][0]}
            if not (ev_pair_tag == pair_tag):
                continue

            stim_event_path = '{}/Stim_Trials/{}.Stim_Event.{}.mat'.format(path_CoreData, subject_id, ev_id+1)
            if not os.path.exists(stim_event_path):
                continue

            # Retrieve raw data
            try:
                df_raw = io.loadmat(stim_event_path)
            except:
                continue
            evData = df_raw['evData'][...].T
            fs = int(np.ceil(df_raw['Fs'][0, 0]))

            # Re-sort electrodes in order of chan_mp
            evData = evData[:, resort_ix]
            n_samp, n_chan = evData.shape

            # Window the stimulation clip
            stim_duration = ev['pulse_duration'][0, 0] / 1000.0
            n_win_dur = int(0.5*fs)

            n_stim_start = int(0.5*fs)
            n_stim_dur = int(stim_duration*fs)
            n_stim_end = n_stim_start + n_stim_dur
            n_stim_pad = int(100/1000.0*fs)

            win_pre_stim = list(np.arange(n_stim_start-n_win_dur, n_stim_start))
            win_post_stim = list(np.arange(n_stim_end+n_stim_pad, n_stim_end+n_stim_pad+n_win_dur))

            # Compute the stim artifact feature (mean amplitude)
            try:
                pre_mean_amp = np.nanmean(evData[win_pre_stim, :], axis=0)
                post_mean_amp = np.nanmean(evData[win_post_stim, :], axis=0)
            except Exception as EXC:
                print('{}: {}'.format(stim_event_path, EXC))
                continue
            pre_stim_mean_amp.append(pre_mean_amp)
            post_stim_mean_amp.append(post_mean_amp)

        pre_stim_mean_amp = np.array(pre_stim_mean_amp)
        post_stim_mean_amp = np.array(post_stim_mean_amp)

        # Conduct a paired t-test per electrode
        for ch_ix in xrange(n_chan):
            ts, pv = stats.ttest_rel(pre_stim_mean_amp[:, ch_ix], post_stim_mean_amp[:, ch_ix])
            if pv < (alpha / n_chan):
                chan_artifact_ix[pair_tag_key].append(chan_mp_lbl[ch_ix])

    return chan_artifact_ix
