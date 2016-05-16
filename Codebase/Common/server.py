'''
Parallel server handling

Created by: Ankit Khambhati

Change Log
----------
2016/02/29 - Start, stop, query ipyparallel server dynamically
'''

import ipyparallel
import subprocess
import time

from . import display
from . import errors


def start_ipcluster(n_proc, profile):
    '''
    Dynamically start an ipcuster server with the desired profile

    Parameters
    ----------
        n_proc: int
            Number of CPU processes to start

        profile: str
            Name of the ipcluster profile
    '''
    errors.check_type(n_proc, int)
    errors.check_type(profile, str)

    display.my_display('\nStarting cluster: {0}\n'.format(profile),
                              True)

    sp_str = 'ipcluster start -n {0} --profile={1}'.format(n_proc,
                                                           profile)
    subprocess.Popen(sp_str, shell=True)
    while True:
        try:
            c = ipyparallel.Client(profile=profile)
            if len(c) < n_proc:
                display.my_display('.', True)
                raise ipyparallel.error.TimeoutError
            c.close()
            break
        except (IOError, ipyparallel.error.TimeoutError):
            display.my_display('.', True)
            time.sleep(1)

    display.my_display('\nDone.\n', True)


def stop_ipcluster(profile):
    '''
    Dynamically stop ipcluster server

    Parameters
    ----------
        profile: str
            Name of the ipcluster profile
    '''
    errors.check_type(profile, str)

    display.my_display('\nStopping cluster: {0}\n'.format(profile),
                              True)

    sp_str = 'ipcluster stop --profile={0}'.format(profile)

    proc = subprocess.Popen(sp_str, shell=True, stderr=subprocess.PIPE)
    line_out = proc.stderr.readline()
    if 'CRITICAL' in line_out:
        display.my_display('No cluster to stop.\n', True)
    elif 'Stopping' in line_out:
        st = time.time()
        display.my_display('Waiting for cluster to stop.\n', True)
        while (time.time() - st) < 4:
            display.my_display('.', True)
            time.sleep(1)
    else:
        display.my_display(
            '**** Unrecognized Syntax in ipcluster output,' +
            'waiting for server to stop anyways ****', True)

    display.my_display('\nDone.\n', True)
