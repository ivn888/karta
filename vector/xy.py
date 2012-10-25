""" Convenience functions for XY(Z) tables. """

import numpy as np

def distance_xy(A):
    """ Calculate the cumulative distance at each coordinate pair in *A*. """
    d_ = np.sqrt(np.sum((A[1:,:] - flowline[:-1,:])**2, axis=1))
    d = [0]
    for a in d_:
        d.append(d[-1]+a)
    return np.array(d)

contains = lambda s, S: s in S

def load_xy(fnm, delimiter=''):
    """ Load a flowline file and return a size-2 array of coordinates. """
    with open(fnm) as f:
        lines = f.readlines()

    if delimiter == '':
        for delimiter in (',', '\t', ' '):
            if contains(delimiter, lines[-1]):
                break
            delimiter = None

    coords = [[float(num) for num in line.split(delimiter)] for line in lines]
    return np.array(coords)


def xyz2array_reg(X, Y, Z):
    """ Return an array from X,Y,Z vectors, assuming gridding is
    regular. """
    xmin = min(X)
    xmax = max(X)
    ymin = min(Y)
    ymax = max(Y)

    nx = sum([y==ymin for y in Y])
    ny = sum([x==xmin for x in X])

    XYZ = [(x,y,z) for x,y,z in zip(X,Y,Z)]
    XYZ.sort(key=lambda a: a[1])
    XYZ.sort(key=lambda a: a[0])
    Zs = [a[2] for a in XYZ]

    A = np.zeros([ny, nx])
    for i in range(ny):
        A[i,:] = Zs[i*nx:(i+1)*nx]

    return A


def array2xyz(A, X, Y):
    """ There are a few occasions when an XYZ list is the proper data
    format. This function converts from an array *A* with coordinates
    defined by *X* and *Y* to a list of (x,y,z) tuples.
    """
    xyz = []
    m, n = A.shape
    for j in range(n):
        for i in range (m):
            xyz.append( (X[i], Y[j], A[i,j]) )
    return xyz

