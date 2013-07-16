# Copyright (c) 2012, GPy authors (see AUTHORS.txt).
# Licensed under the BSD 3-clause license (see LICENSE.txt)

import numpy as np
from scipy import weave

def opt_wrapper(m, **kwargs):
    """
    This function just wraps the optimization procedure of a GPy
    object so that optimize() pickleable (necessary for multiprocessing).
    """
    m.optimize(**kwargs)
    return m.optimization_runs[-1]


def linear_grid(D, n = 100, min_max = (-100, 100)):
    """
    Creates a D-dimensional grid of n linearly spaced points

    Parameters:

    D:        dimension of the grid
    n:        number of points
    min_max:  (min, max) list


    """

    g = np.linspace(min_max[0], min_max[1], n)
    G = np.ones((n, D))

    return G*g[:,None]

def kmm_init(X, m = 10):
    """
    This is the same initialization algorithm that is used
    in Kmeans++. It's quite simple and very useful to initialize
    the locations of the inducing points in sparse GPs.

    :param X: data
    :param m: number of inducing points
    """

    # compute the distances
    XXT = np.dot(X, X.T)
    D = (-2.*XXT + np.diag(XXT)[:,np.newaxis] + np.diag(XXT)[np.newaxis,:])

    # select the first point
    s = np.random.permutation(X.shape[0])[0]
    inducing = [s]
    prob = D[s]/D[s].sum()

    for z in range(m-1):
        s = np.random.multinomial(1, prob.flatten()).argmax()
        inducing.append(s)
        prob = D[s]/D[s].sum()

    inducing = np.array(inducing)
    return X[inducing]

def fast_array_equal(A, B):
    code="""
    int i, j;
    return_val = 1;

    #pragma omp parallel for private(i, j)
    for(i=0;i<N;i++){
       for(j=0;j<D;j++){
          if(A(i, j) != B(i, j)){
              return_val = 0;
              break;
          }
       }
    }
    """

    support_code = """
    #include <omp.h>
    #include <math.h>
    """

    weave_options = {'headers'           : ['<omp.h>'],
                     'extra_compile_args': ['-fopenmp -O3'],
                     'extra_link_args'   : ['-lgomp']}


    value = False

    if A is not None and B is not None and A.shape == B.shape:
        if len(A.shape) == 2:
            N, D = A.shape
            value = weave.inline(code, support_code=support_code, libraries=['gomp'],
                                 arg_names=['A', 'B', 'N', 'D'],
                                 type_converters=weave.converters.blitz,**weave_options)
        else:
            value = np.array_equal(A,B)


    return value


if __name__ == '__main__':
    import pylab as plt
    X = np.linspace(1,10, 100)[:, None]
    X = X[np.random.permutation(X.shape[0])[:20]]
    inducing = kmm_init(X, m = 5)
    plt.figure()
    plt.plot(X.flatten(), np.ones((X.shape[0],)), 'x')
    plt.plot(inducing, 0.5* np.ones((len(inducing),)), 'o')
    plt.ylim((0.0, 10.0))
