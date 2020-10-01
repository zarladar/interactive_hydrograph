import h5py
import numpy as np


def get_4d_array(hdf5, model_dim):
    h5 = h5py.File(hdf5, 'r')

    heads_2d = np.array(h5['/Datasets/Head/Values'])
    heads_4d = heads_2d[..., np.newaxis, np.newaxis]

    periods = heads_4d.shape[0]
    rows, cols, lays = model_dim

    heads_4d = heads_4d.reshape((periods, lays, rows, cols))
    return heads_4d
