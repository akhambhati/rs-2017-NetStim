from __future__ import division
import numpy as np
import scipy.linalg as scila


def average_control(A):
    '''
    FUNCTION:
     Returns values of AVERAGE CONTROLLABILITY for each node in a
     network, given the adjacency matrix for that network. Average
     controllability indicates the ability of that node to steer the
     system into difficult-to-reach states, given input at that node.

    INPUT:
     A is the structural (NOT FUNCTIONAL) network adjacency matrix,
     such that the simple linear model of dynamics outlined in the
     reference is an accurate estimate of brain state fluctuations.
     Assumes all values in the matrix are positive, and that the
     matrix is symmetric.

    OUTPUT:
     Vector of average controllability values for each node

    Bassett Lab, University of Pennsylvania, 2016.
    Reference: Gu, Pasqualetti, Cieslak, Telesford, Yu, Kahn, Medaglia,
               Vettel, Miller, Grafton & Bassett, Nature Communications 6:8414, 2015.
    '''

    # Normalize the matrix based on largest singular value
    A = A / (1 + np.linalg.svd(A)[1][0])

    # Evaluate schur stability
    T, U = scila.schur(A, 'real')
    midMat = (U**2)

    v = np.expand_dims(np.diag(T), axis=1)
    v = np.dot(v, v.T)
    P = np.tile(np.diag(1-v), (v.shape[0], 1))

    vals = np.sum(midMat/P, axis=1)
    return vals


def modal_control(A):
    '''
    FUNCTION:
     Returns values of MODAL CONTROLLABILITY for each node in a
     network, given the adjacency matrix for that network. Modal
     controllability indicates the ability of that node to steer the
     system into difficult-to-reach states, given input at that node.

    INPUT:
     A is the structural (NOT FUNCTIONAL) network adjacency matrix,
     such that the simple linear model of dynamics outlined in the
     reference is an accurate estimate of brain state fluctuations.
     Assumes all values in the matrix are positive, and that the
     matrix is symmetric.

    OUTPUT:
     Vector of modal controllability values for each node

    Bassett Lab, University of Pennsylvania, 2016.
    Reference: Gu, Pasqualetti, Cieslak, Telesford, Yu, Kahn, Medaglia,
               Vettel, Miller, Grafton & Bassett, Nature Communications 6:8414, 2015.
    '''

    # Normalize the matrix based on largest singular value
    A = A / (1 + np.linalg.svd(A)[1][0])

    # Evaluate schur stability
    T, U = scila.schur(A, 'real')
    eigVals = np.diag(T);

    N = A.shape[0]
    phi = np.zeros(N)
    for ii in xrange(N):
        phi[ii] = np.dot(U[ii, :]**2, 1 - eigVals**2)

    return phi
