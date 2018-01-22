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
path_ExpData = path_PeriphData + '/e00-Clean_Channels'

for path in [path_CoreData, path_PeriphData, path_ExpData]:
    if not os.path.exists(path):
        print('Path: {}, does not exist'.format(path))
        os.makedirs(path)

# Data manipulation imports
import numpy as np
import Echobase
import handle_bad_channels
#### ---------------------- Front Matter ------------------------

def run(subj_id):
    # Clean the channels for this subject
    monopolar_id, monopolar_lbl, monopolar_resort_ix = handle_bad_channels.init_channels(subj_id)
    monopolar_lbl_artifact = handle_bad_channels.find_stim_artifact(subj_id)

    monopolar_id_artifact = {}
    for stim_tag in monopolar_lbl_artifact.keys():
        monopolar_id_artifact[stim_tag] = np.unique(
            handle_bad_channels.find_index_in_list(monopolar_lbl,
                                                   monopolar_lbl_artifact[stim_tag]))

    return monopolar_id, monopolar_lbl, monopolar_id_artifact, monopolar_lbl_artifact, monopolar_resort_ix


if __name__ == '__main__':
    # Grab the Task ID from QSUB
    sge_task_id = int(os.environ['SGE_TASK_ID'])-1

    # Load the file list
    proc_list = pkl.load(open('{}/proc_list.pkl'.format(path_ExpData), 'r'))
    subj_id = proc_list[sge_task_id]

    # Run and cache output
    foutput = '{}/Clean_Channels.{}.npz'.format(path_ExpData, subj_id)
    if os.path.exists(foutput):
        print('Output file already exists: {}'.format(foutput))
        sys.exit()
    monopolar_id, monopolar_lbl, monopolar_id_artifact, monopolar_lbl_artifact, monopolar_resort_ix = run(subj_id)
    np.savez(foutput,
             monopolar_id=monopolar_id,
             monopolar_lbl=monopolar_lbl,
             monopolar_id_artifact=monopolar_id_artifact,
             monopolar_lbl_artifact=monopolar_lbl_artifact,
             monopolar_resort_ix=monopolar_resort_ix)

"
